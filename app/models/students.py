from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.attendances import Attendance
    from app.models.enrollments import StudentClassEnrollment
    from app.models.gate_attendances import GateAttendance
    from app.models.student_faces import StudentFace


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nis: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    guardian_phone: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    enrollments: Mapped[list["StudentClassEnrollment"]] = relationship(
        back_populates="student"
    )
    faces: Mapped[list["StudentFace"]] = relationship(back_populates="student")
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="student"
    )
    gate_attendances: Mapped[list["GateAttendance"]] = relationship(
        back_populates="student"
    )
