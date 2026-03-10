from __future__ import annotations

import uuid
from datetime import datetime
from datetime import time as dt_time

from app.db.base import Base
from sqlalchemy import DateTime, String, Time, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class SchoolSetting(Base):
    __tablename__ = "school_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        default="default",
    )
    gate_in_time: Mapped[dt_time] = mapped_column(
        Time,
        nullable=False,
        default=dt_time(hour=7, minute=0, second=0),
    )
    gate_out_time: Mapped[dt_time] = mapped_column(
        Time,
        nullable=False,
        default=dt_time(hour=15, minute=0, second=0),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

