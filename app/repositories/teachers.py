from __future__ import annotations

import uuid

from app.models import Teacher
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload


class TeacherRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, teacher: Teacher) -> None:
        self.db.add(teacher)

    def delete(self, teacher: Teacher) -> None:
        self.db.delete(teacher)

    def get(self, teacher_id: uuid.UUID) -> Teacher | None:
        stmt = (
            select(Teacher)
            .options(joinedload(Teacher.user))
            .where(Teacher.id == teacher_id)
        )
        return self.db.scalar(stmt)

    def get_by_user_id(self, user_id: uuid.UUID) -> Teacher | None:
        stmt = select(Teacher).where(Teacher.user_id == user_id)
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Teacher], int]:
        stmt = select(Teacher).options(joinedload(Teacher.user))
        total_stmt = select(func.count()).select_from(Teacher)
        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt
            .order_by(Teacher.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def list_options(self) -> list[Teacher]:
        stmt = select(Teacher).order_by(Teacher.name.asc())
        return list(self.db.scalars(stmt))
