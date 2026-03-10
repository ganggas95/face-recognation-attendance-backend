from __future__ import annotations

import uuid

from app.models import AcademicYear, ClassInstance, StudentClassEnrollment
from sqlalchemy import select
from sqlalchemy.orm import Session


class EnrollmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, enrollment: StudentClassEnrollment) -> None:
        self.db.add(enrollment)

    def get_by_student_class_instance(
        self,
        *,
        student_id: uuid.UUID,
        class_instance_id: uuid.UUID,
    ) -> StudentClassEnrollment | None:
        stmt = select(StudentClassEnrollment).where(
            StudentClassEnrollment.student_id == student_id,
            StudentClassEnrollment.class_instance_id == class_instance_id,
        )
        return self.db.scalar(stmt)

    def list_student_ids_by_class_instance(
        self,
        *,
        class_instance_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        stmt = select(StudentClassEnrollment.student_id).where(
            StudentClassEnrollment.class_instance_id == class_instance_id
        )
        return list(self.db.scalars(stmt))

    def list_by_student_ids(
        self,
        *,
        student_ids: list[uuid.UUID] | None = None,
        active_academic_year_only: bool = True,
    ) -> list[StudentClassEnrollment]:
        stmt = select(StudentClassEnrollment)
        if student_ids:
            stmt = stmt.where(
                StudentClassEnrollment.student_id.in_(student_ids)
            )
        if active_academic_year_only:
            stmt = (
                stmt.join(StudentClassEnrollment.class_instance)
                .join(ClassInstance.academic_year)
                .where(AcademicYear.is_active.is_(True))
            )
        stmt = stmt.order_by(StudentClassEnrollment.created_at.desc())
        return list(self.db.scalars(stmt))
