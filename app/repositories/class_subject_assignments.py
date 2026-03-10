from __future__ import annotations

import uuid

from app.models import ClassInstance, ClassSubjectAssignment
from app.models.academic_years import AcademicYear
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload


class ClassSubjectAssignmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, assignment: ClassSubjectAssignment) -> None:
        self.db.add(assignment)

    def delete(self, assignment: ClassSubjectAssignment) -> None:
        self.db.delete(assignment)

    def get(
        self, assignment_id: uuid.UUID
    ) -> ClassSubjectAssignment | None:
        return self.db.get(ClassSubjectAssignment, assignment_id)

    def get_by_class_instance_subject(
        self,
        *,
        class_instance_id: uuid.UUID,
        subject_id: uuid.UUID,
    ) -> ClassSubjectAssignment | None:
        stmt = select(ClassSubjectAssignment).where(
            ClassSubjectAssignment.class_instance_id == class_instance_id,
            ClassSubjectAssignment.subject_id == subject_id,
        )
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        class_instance_id: uuid.UUID | None = None,
        teacher_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
    ) -> tuple[list[ClassSubjectAssignment], int]:
        stmt = select(ClassSubjectAssignment)
        total_stmt = select(func.count()).select_from(ClassSubjectAssignment)

        if class_instance_id:
            stmt = stmt.where(
                ClassSubjectAssignment.class_instance_id == class_instance_id
            )
            total_stmt = total_stmt.where(
                ClassSubjectAssignment.class_instance_id == class_instance_id
            )
        if teacher_id:
            stmt = stmt.where(ClassSubjectAssignment.teacher_id == teacher_id)
            total_stmt = total_stmt.where(
                ClassSubjectAssignment.teacher_id == teacher_id
            )
        if subject_id:
            stmt = stmt.where(ClassSubjectAssignment.subject_id == subject_id)
            total_stmt = total_stmt.where(
                ClassSubjectAssignment.subject_id == subject_id
            )

        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.order_by(ClassSubjectAssignment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total

    def list_options(
        self,
        *,
        active_academic_year_only: bool = True,
    ) -> list[ClassSubjectAssignment]:
        stmt = select(ClassSubjectAssignment).options(
            joinedload(ClassSubjectAssignment.class_instance).joinedload(
                ClassInstance.class_template
            ),
            joinedload(ClassSubjectAssignment.class_instance).joinedload(
                ClassInstance.academic_year
            ),
            joinedload(ClassSubjectAssignment.subject),
            joinedload(ClassSubjectAssignment.teacher),
        )

        if active_academic_year_only:
            stmt = (
                stmt.join(ClassSubjectAssignment.class_instance)
                .join(ClassInstance.academic_year)
                .where(AcademicYear.is_active.is_(True))
            )

        stmt = stmt.order_by(ClassSubjectAssignment.created_at.desc())
        return list(self.db.scalars(stmt))
