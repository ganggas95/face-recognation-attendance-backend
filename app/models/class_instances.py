from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.academic_years import AcademicYear
    from app.models.class_subject_assignments import ClassSubjectAssignment
    from app.models.class_subject_schedules import ClassSubjectSchedule
    from app.models.classes import Class
    from app.models.enrollments import StudentClassEnrollment


class ClassInstance(Base):
    __tablename__ = "class_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    class_template: Mapped["Class"] = relationship(
        back_populates="class_instances"
    )
    academic_year: Mapped["AcademicYear"] = relationship(
        back_populates="class_instances"
    )
    enrollments: Mapped[list["StudentClassEnrollment"]] = relationship(
        back_populates="class_instance"
    )
    subject_assignments: Mapped[list["ClassSubjectAssignment"]] = relationship(
        back_populates="class_instance"
    )
    subject_schedules: Mapped[list["ClassSubjectSchedule"]] = relationship(
        back_populates="class_instance",
    )
