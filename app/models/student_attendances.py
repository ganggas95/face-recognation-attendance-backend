from __future__ import annotations

import uuid
from datetime import date as dt_date
from datetime import datetime
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import (Boolean, Date, DateTime, ForeignKey, String,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.gate_attendances import GateAttendance
    from app.models.students import Student
    from app.models.users import User


class StudentAttendance(Base):
    __tablename__ = "student_attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "date",
            name="uq_student_attendance_student_date",
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
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)

    checkin_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_attendances.id", ondelete="SET NULL"),
        nullable=True,
    )
    checkout_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_attendances.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False)
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    student: Mapped["Student"] = relationship()
    checkin: Mapped["GateAttendance | None"] = relationship(
        foreign_keys=[checkin_id]
    )
    checkout: Mapped["GateAttendance | None"] = relationship(
        foreign_keys=[checkout_id]
    )
    verified_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[verified_by]
    )

