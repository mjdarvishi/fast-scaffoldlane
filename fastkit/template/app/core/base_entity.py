import inspect
import sys
import types
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T", bound="BaseEntity")


class BaseEntity:
    """Universal BaseEntity with from_dict, to_json, and exclude support."""

    @classmethod
    def _resolved_field_types(cls) -> dict[str, Any]:
        """Resolve annotations without letting one missing forward reference spoil all fields."""
        known_entities: dict[str, type[BaseEntity]] = {}
        pending = list(BaseEntity.__subclasses__())
        while pending:
            entity_type = pending.pop()
            known_entities[entity_type.__name__] = entity_type
            pending.extend(entity_type.__subclasses__())

        try:
            return get_type_hints(cls, localns=known_entities)
        except NameError:
            module_globals = vars(sys.modules[cls.__module__])
            resolved: dict[str, Any] = {}
            for name, annotation in getattr(cls, "__annotations__", {}).items():
                if not isinstance(annotation, str):
                    resolved[name] = annotation
                    continue

                annotation_holder = type(
                    "_FieldAnnotation",
                    (),
                    {"__annotations__": {"value": annotation}},
                )
                try:
                    resolved[name] = get_type_hints(
                        annotation_holder,
                        globalns=module_globals,
                        localns=known_entities,
                    )["value"]
                except NameError:
                    resolved[name] = annotation
            return resolved

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        if not data:
            return None  # type: ignore

        field_types = cls._resolved_field_types()
        init_data = {}

        for f in fields(cls):
            name = f.name
            field_type = field_types.get(name, f.type)
            value = data.get(name)

            if value is None:
                init_data[name] = None
                continue

            origin = get_origin(field_type)
            args = get_args(field_type)

            # -------------------------
            # Handle Optional[T]
            # -------------------------
            if origin in (Union, types.UnionType) and type(None) in args:
                non_none_args = [a for a in args if a is not type(None)]
                if len(non_none_args) == 1:
                    field_type = non_none_args[0]
                    origin = get_origin(field_type)
                    args = get_args(field_type)

            # -------------------------
            # Handle List[T]
            # -------------------------
            if origin is list:
                inner_type = args[0]

                if isinstance(value, list):
                    new_list = []
                    for item in value:
                        # Nested Entity / Dataclass
                        if (
                            isinstance(inner_type, type)
                            and (is_dataclass(inner_type) or issubclass(inner_type, BaseEntity))
                            and isinstance(item, dict)
                        ):
                            new_list.append(inner_type.from_dict(item))

                        # Enum inside list
                        elif isinstance(inner_type, type) and issubclass(inner_type, Enum):
                            try:
                                new_list.append(inner_type(item))
                            except Exception:
                                new_list.append(inner_type[str(item)])

                        else:
                            new_list.append(item)

                    init_data[name] = new_list
                else:
                    init_data[name] = value

                continue

            # -------------------------
            # Handle nested dataclass / BaseEntity
            # -------------------------
            if (
                isinstance(field_type, type)
                and (is_dataclass(field_type) or issubclass(field_type, BaseEntity))
                and isinstance(value, dict)
            ):
                init_data[name] = field_type.from_dict(value)
                continue

            # -------------------------
            # Handle Enum
            # -------------------------
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                if isinstance(value, field_type):
                    init_data[name] = value
                else:
                    try:
                        init_data[name] = field_type(value)  # by value
                    except Exception as exc:
                        try:
                            init_data[name] = field_type[str(value)]  # by name
                        except Exception:
                            raise ValueError(
                                f"Invalid value '{value}' for enum {field_type.__name__}"
                            ) from exc
                continue

            # -------------------------
            # Handle datetime / date
            # -------------------------
            if field_type in (datetime, date) and isinstance(value, str):
                try:
                    init_data[name] = field_type.fromisoformat(value)
                    continue
                except Exception:
                    pass

            # -------------------------
            # Handle Decimal
            # -------------------------
            if field_type is Decimal and isinstance(value, (str, int, float)):
                try:
                    init_data[name] = Decimal(value)
                    continue
                except Exception:
                    pass

            # -------------------------
            # Handle UUID
            # -------------------------
            if field_type is UUID and isinstance(value, str):
                init_data[name] = UUID(value)
                continue

            # -------------------------
            # Fallback
            # -------------------------
            init_data[name] = value

        return cls(**init_data)  # type: ignore

    def to_dict(self, exclude=None):
        """
        Convert dataclass/BaseEntity to dict, handling nested dataclasses and BaseEntity
        recursively. Supports exclude as a list of field paths.
        """
        from datetime import date, datetime
        from decimal import Decimal
        from enum import Enum

        def parse_exclude(exclude):
            tree = {}
            if exclude:
                for item in exclude:
                    parts = item.split(".")
                    current = tree
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            if part not in current:
                                current[part] = None
                        else:
                            if part not in current or current[part] is None:
                                current[part] = {}
                            current = current[part]
            return tree

        def recursive_to_dict(obj, exclude_tree=None):
            # Pydantic model
            if isinstance(obj, BaseModel):
                return obj.model_dump(exclude_unset=False)

            # Dataclass or BaseEntity
            if is_dataclass(obj) or isinstance(obj, BaseEntity):
                result = {}
                for f in fields(obj):
                    k = f.name
                    v = getattr(obj, k)
                    if v is None:
                        continue
                    sub_exclude = (
                        exclude_tree.get(k) if exclude_tree and k in exclude_tree else None
                    )
                    if isinstance(v, (datetime, date)):
                        result[k] = v.isoformat()
                    elif isinstance(v, UUID):
                        result[k] = str(v)
                    elif isinstance(v, Enum):
                        result[k] = v.value
                    elif isinstance(v, Decimal):
                        result[k] = float(v)
                    elif is_dataclass(v) or isinstance(v, BaseEntity):
                        result[k] = recursive_to_dict(v, sub_exclude)
                    elif isinstance(v, list):
                        result[k] = [recursive_to_dict(item, sub_exclude) for item in v]
                    else:
                        result[k] = v
                # Add properties
                for name, _value in inspect.getmembers(
                    type(obj), lambda o: isinstance(o, property)
                ):
                    prop_value = getattr(obj, name)
                    if prop_value is not None:
                        if exclude_tree and name in exclude_tree and exclude_tree[name] is None:
                            continue
                        result[name] = prop_value
                # Exclude fields
                if exclude_tree:
                    for key in list(result.keys()):
                        if key in exclude_tree and exclude_tree[key] is None:
                            result.pop(key, None)
                return result

            # List
            if isinstance(obj, list):
                return [recursive_to_dict(item, exclude_tree) for item in obj]

            if isinstance(obj, UUID):
                return str(obj)

            if isinstance(obj, Decimal):
                return float(obj)

            return obj

        exclude_tree = parse_exclude(exclude)
        return recursive_to_dict(self, exclude_tree)
