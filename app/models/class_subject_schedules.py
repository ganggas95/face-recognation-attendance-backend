from __future__ import annotations

import uuid
from datetime import datetime, time as dt_time
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import (DateTime, ForeignKey, Integer, String, Time,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.attendances import Attendance
    from app.models.class_instances import ClassInstance
    from app.models.class_subject_assignments import ClassSubjectAssignment
    from app.models.subjects import Subject
    from app.models.teachers import Teacher


class ClassSubjectSchedule(Base):
    __tablename__ = "class_subject_schedules"
    __table_args__ = (
        UniqueConstraint(
            "class_instance_id",
            "day_of_week",
            "start_time",
            name="uq_class_schedule_slot",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    class_instance_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_instances.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_subject_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_subject_assignments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    end_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    class_instance: Mapped["ClassInstance"] = relationship(
        back_populates="subject_schedules",
    )
    class_subject_assignment: Mapped["ClassSubjectAssignment | None"] = (
        relationship(back_populates="schedules")
    )
    subject: Mapped["Subject"] = relationship(back_populates="schedules")
    teacher: Mapped["Teacher"] = relationship(
        back_populates="subject_schedules",
    )
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="schedule",
    )
