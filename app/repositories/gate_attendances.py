from __future__ import annotations

import uuid
from datetime import date as dt_date

from app.models import GateAttendance, Student
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload


class GateAttendanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: GateAttendance) -> None:
        self.db.add(item)

    def get_by_student_date_direction(
        self,
        *,
        student_id: uuid.UUID,
        date: dt_date,
        direction: str,
    ) -> GateAttendance | None:
        stmt = select(GateAttendance).where(
            GateAttendance.student_id == student_id,
            GateAttendance.date == date,
            GateAttendance.direction == direction,
        )
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        date: dt_date | None = None,
        direction: str | None = None,
        student_name: str | None = None,
        recorded_by_user_id: uuid.UUID | None = None,
    ) -> tuple[list[GateAttendance], int]:
        stmt = (
            select(GateAttendance)
            .join(GateAttendance.student)
            .join(GateAttendance.recorded_by_user)
        )
        total_stmt = (
            select(func.count())
            .select_from(GateAttendance)
            .join(GateAttendance.student)
            .join(GateAttendance.recorded_by_user)
        )

        if date is not None:
            stmt = stmt.where(GateAttendance.date == date)
            total_stmt = total_stmt.where(GateAttendance.date == date)

        if direction is not None:
            d = direction.strip()
            if d:
                stmt = stmt.where(GateAttendance.direction == d)
                total_stmt = total_stmt.where(GateAttendance.direction == d)

        if recorded_by_user_id is not None:
            stmt = stmt.where(
                GateAttendance.recorded_by_user_id == recorded_by_user_id
            )
            total_stmt = total_stmt.where(
                GateAttendance.recorded_by_user_id == recorded_by_user_id
            )

        if student_name:
            q = student_name.strip()
            if q:
                like = f"%{q}%"
                stmt = stmt.where(Student.name.ilike(like))
                total_stmt = total_stmt.where(Student.name.ilike(like))

        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.options(
                joinedload(GateAttendance.student),
                joinedload(GateAttendance.recorded_by_user),
            )
            .order_by(
                GateAttendance.date.desc(),
                GateAttendance.time.desc(),
                GateAttendance.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).unique())
        return items, total
