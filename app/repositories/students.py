from __future__ import annotations

from app.models import Student
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, student: Student) -> None:
        self.db.add(student)

    def get(self, student_id) -> Student | None:
        return self.db.get(Student, student_id)

    def get_by_nis(self, nis: str) -> Student | None:
        stmt = select(Student).where(Student.nis == nis)
        return self.db.scalar(stmt)

    def list(self) -> list[Student]:
        stmt = select(Student).order_by(Student.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Student], int]:
        total_stmt = select(func.count()).select_from(Student)
        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            select(Student)
            .order_by(Student.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total
