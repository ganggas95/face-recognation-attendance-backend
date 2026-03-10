from __future__ import annotations

import uuid
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import (Date, DateTime, Float, ForeignKey, String, Time,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.students import Student
    from app.models.users import User


class GateAttendance(Base):
    __tablename__ = "gate_attendances"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "date",
            "direction",
            name="uq_gate_attendance_student_date_direction",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    student: Mapped["Student"] = relationship(
        back_populates="gate_attendances"
    )
    recorded_by_user: Mapped["User"] = relationship(
        back_populates="recorded_gate_attendances",
    )
