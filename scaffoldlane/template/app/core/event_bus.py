from typing import Type, Callable, Dict, List, TypeVar, Generic, Any
import asyncio
from app.core.database.transaction_manager import session_var
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependency import injector
from app.core.logging.logging_config import LogConfig

logger = LogConfig.get_app_logger()
TEvent = TypeVar("TEvent", bound="BaseEvent")


class BaseEvent:
    """Base class for domain/application events."""


class BaseListener(Generic[TEvent]):
    """Base listener that auto-subscribes itself to EventBus on init."""

    event_type: Type[TEvent]

    def __init__(self):
        if not hasattr(self, "event_type") or self.event_type is None:
            raise ValueError(f"{self.__class__.__name__} must define 'event_type'")
        EventBus.subscribe(self.event_type, self.handle)

    def handle(self, event: TEvent) -> Any:
        raise NotImplementedError


class EventBus:
    _subscribers: Dict[Type, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: Type, handler: Callable):
        cls._subscribers.setdefault(event_type, []).append(handler)

    @classmethod
    def publish_async(cls, event):
        event_type = type(event)
        if event_type in cls._subscribers:
            for handler in cls._subscribers[event_type]:

                async def handler_with_new_session(event, handler):
                    session = injector.get(AsyncSession)
                    session_var.set(session)
                    try:
                        maybe_result = handler(event)
                        if asyncio.iscoroutine(maybe_result):
                            await maybe_result
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Error in async event handler: {e}", exc_info=True)
                    finally:
                        await session.close()

                try:
                    asyncio.create_task(handler_with_new_session(event, handler))
                except RuntimeError:
                    logger.warning(
                        f"No event loop running, skipping async event scheduling for {event_type.__name__}"
                    )

    @classmethod
    def publish_sync(cls, event):
        event_type = type(event)
        if event_type in cls._subscribers:
            for handler in cls._subscribers[event_type]:
                handler(event)
