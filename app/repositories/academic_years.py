from __future__ import annotations

import uuid

from app.models import AcademicYear
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session


class AcademicYearRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, academic_year: AcademicYear) -> None:
        self.db.add(academic_year)

    def get(self, academic_year_id: uuid.UUID) -> AcademicYear | None:
        return self.db.get(AcademicYear, academic_year_id)

    def list(self) -> list[AcademicYear]:
        stmt = select(AcademicYear).order_by(AcademicYear.start_date.desc())
        return list(self.db.scalars(stmt))

    def get_active(self) -> AcademicYear | None:
        stmt = select(AcademicYear).where(AcademicYear.is_active.is_(True))
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[AcademicYear], int]:
        total_stmt = select(func.count()).select_from(AcademicYear)
        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            select(AcademicYear)
            .order_by(AcademicYear.start_date.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def deactivate_all(self) -> None:
        self.db.execute(update(AcademicYear).values(is_active=False))
