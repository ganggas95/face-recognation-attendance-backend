from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.classes import Class
    from app.models.class_subject_assignments import ClassSubjectAssignment
    from app.models.class_subject_schedules import ClassSubjectSchedule
    from app.models.subjects import Subject
    from app.models.users import User


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    nip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="teacher")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="teacher")
    subject_assignments: Mapped[list["ClassSubjectAssignment"]] = relationship(
        back_populates="teacher",
    )
    subject_schedules: Mapped[list["ClassSubjectSchedule"]] = relationship(
        back_populates="teacher",
    )
    homeroom_classes: Mapped[list["Class"]] = relationship(
        back_populates="homeroom_teacher",
        foreign_keys="Class.homeroom_teacher_id",
    )
