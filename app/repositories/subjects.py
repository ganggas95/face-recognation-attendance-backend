from __future__ import annotations

import uuid

from app.models import Subject
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload


class SubjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, subject: Subject) -> None:
        self.db.add(subject)

    def get(self, subject_id: uuid.UUID) -> Subject | None:
        return self.db.get(Subject, subject_id)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        teacher_id: uuid.UUID | None = None,
    ) -> tuple[list[Subject], int]:
        stmt = select(Subject).options(joinedload(Subject.teacher))
        total_stmt = select(func.count()).select_from(Subject)
        if teacher_id:
            stmt = stmt.where(Subject.teacher_id == teacher_id)
            total_stmt = total_stmt.where(Subject.teacher_id == teacher_id)
        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.order_by(Subject.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def list_options(self) -> list[Subject]:
        stmt = select(Subject)
        stmt = stmt.order_by(Subject.name.asc())
        return list(self.db.scalars(stmt))

    def list_options_by_teacher_id(
        self,
        *,
        teacher_id: uuid.UUID,
    ) -> list[Subject]:
        stmt = (
            select(Subject)
            .where(Subject.teacher_id == teacher_id)
            .order_by(Subject.name.asc())
        )
        return list(self.db.scalars(stmt))
