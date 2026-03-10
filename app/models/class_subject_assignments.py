from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.class_instances import ClassInstance
    from app.models.class_subject_schedules import ClassSubjectSchedule
    from app.models.subjects import Subject
    from app.models.teachers import Teacher


class ClassSubjectAssignment(Base):
    __tablename__ = "class_subject_assignments"
    __table_args__ = (
        UniqueConstraint(
            "class_instance_id",
            "subject_id",
            name="uq_class_subject_assignment",
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    class_instance: Mapped["ClassInstance"] = relationship(
        back_populates="subject_assignments"
    )
    subject: Mapped["Subject"] = relationship(back_populates="assignments")
    teacher: Mapped["Teacher"] = relationship(
        back_populates="subject_assignments"
    )
    schedules: Mapped[list["ClassSubjectSchedule"]] = relationship(
        back_populates="class_subject_assignment"
    )
