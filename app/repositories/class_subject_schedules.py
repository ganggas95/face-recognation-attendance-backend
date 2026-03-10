from __future__ import annotations

import uuid

from app.models import ClassInstance, ClassSubjectSchedule
from app.models.academic_years import AcademicYear
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload


class ClassSubjectScheduleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, schedule: ClassSubjectSchedule) -> None:
        self.db.add(schedule)

    def get(self, schedule_id: uuid.UUID) -> ClassSubjectSchedule | None:
        return self.db.get(ClassSubjectSchedule, schedule_id)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        class_instance_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        day_of_week: int | None = None,
    ) -> tuple[list[ClassSubjectSchedule], int]:
        stmt = select(ClassSubjectSchedule)
        total_stmt = select(func.count()).select_from(ClassSubjectSchedule)

        if class_instance_id:
            stmt = stmt.where(
                ClassSubjectSchedule.class_instance_id == class_instance_id
            )
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.class_instance_id == class_instance_id
            )
        if teacher_id:
            stmt = stmt.where(ClassSubjectSchedule.teacher_id == teacher_id)
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.teacher_id == teacher_id
            )
        if day_of_week is not None:
            stmt = stmt.where(ClassSubjectSchedule.day_of_week == day_of_week)
            total_stmt = total_stmt.where(
                ClassSubjectSchedule.day_of_week == day_of_week
            )

        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.order_by(
                ClassSubjectSchedule.day_of_week.asc(),
                ClassSubjectSchedule.start_time.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def list_options(
        self,
        *,
        active_academic_year_only: bool = True,
        teacher_id: uuid.UUID | None = None,
    ) -> list[ClassSubjectSchedule]:
        stmt = select(ClassSubjectSchedule).options(
            joinedload(ClassSubjectSchedule.class_instance).joinedload(
                ClassInstance.class_template
            ),
            joinedload(ClassSubjectSchedule.class_instance).joinedload(
                ClassInstance.academic_year
            ),
            joinedload(ClassSubjectSchedule.subject),
            joinedload(ClassSubjectSchedule.teacher),
            joinedload(ClassSubjectSchedule.class_subject_assignment),
        )

        if teacher_id:
            stmt = stmt.where(ClassSubjectSchedule.teacher_id == teacher_id)

        if active_academic_year_only:
            stmt = (
                stmt.join(ClassSubjectSchedule.class_instance)
                .join(ClassInstance.academic_year)
                .where(AcademicYear.is_active.is_(True))
            )

        stmt = stmt.order_by(
            ClassSubjectSchedule.day_of_week.asc(),
            ClassSubjectSchedule.start_time.asc(),
        )
        return list(self.db.scalars(stmt))
