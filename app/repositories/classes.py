from __future__ import annotations

import uuid

from app.models import Class
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class ClassRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, class_template: Class) -> None:
        self.db.add(class_template)

    def delete(self, class_template: Class) -> None:
        self.db.delete(class_template)

    def get(self, class_id: uuid.UUID) -> Class | None:
        return self.db.get(Class, class_id)

    def list(self) -> list[Class]:
        stmt = select(Class).order_by(Class.grade.asc(), Class.name.asc())
        return list(self.db.scalars(stmt))

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Class], int]:
        total_stmt = select(func.count()).select_from(Class)
        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            select(Class)
            .order_by(Class.grade.asc(), Class.name.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total
