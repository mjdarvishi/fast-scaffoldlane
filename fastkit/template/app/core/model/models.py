"""
Sql alchemy entities
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, as_declarative, mapped_column


@as_declarative()
class Base:
    id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        index=True,
    )
    created_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_date: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp()
    )
