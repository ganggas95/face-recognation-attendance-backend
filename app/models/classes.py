from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.db.base import Base
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.class_instances import ClassInstance
    from app.models.teachers import Teacher


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    homeroom_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    class_instances: Mapped[list["ClassInstance"]] = relationship(
        back_populates="class_template"
    )
    homeroom_teacher: Mapped["Teacher | None"] = relationship(
        back_populates="homeroom_classes",
        foreign_keys=[homeroom_teacher_id],
    )
