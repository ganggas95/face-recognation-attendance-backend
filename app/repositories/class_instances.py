from __future__ import annotations

import uuid

from app.models import Class, ClassInstance, ClassSubjectSchedule
from app.models.academic_years import AcademicYear
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload


class ClassInstanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, class_instance: ClassInstance) -> None:
        self.db.add(class_instance)

    def get(self, class_instance_id) -> ClassInstance | None:
        return self.db.get(ClassInstance, class_instance_id)

    def get_by_class_academic_year(
        self,
        *,
        class_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> ClassInstance | None:
        stmt = select(ClassInstance).where(
            ClassInstance.class_id == class_id,
            ClassInstance.academic_year_id == academic_year_id,
        )
        return self.db.scalar(stmt)

    def ensure_active_year_instances(self) -> int:
        active_year = self.db.scalar(
            select(AcademicYear).where(AcademicYear.is_active.is_(True))
        )
        if not active_year:
            return 0

        missing_stmt = select(Class).where(
            ~exists(
                select(1).where(
                    ClassInstance.class_id == Class.id,
                    ClassInstance.academic_year_id == active_year.id,
                )
            )
        )
        missing_classes = list(self.db.scalars(missing_stmt))
        for cls in missing_classes:
            self.db.add(
                ClassInstance(
                    class_id=cls.id,
                    academic_year_id=active_year.id,
                )
            )
        if missing_classes:
            self.db.commit()
        return len(missing_classes)

    def list_options(
        self,
        *,
        active_academic_year_only: bool = True,
        teacher_id: uuid.UUID | None = None,
    ) -> list[ClassInstance]:
        stmt = (
            select(ClassInstance)
            .join(ClassInstance.academic_year)
            .join(ClassInstance.class_template)
            .options(
                joinedload(ClassInstance.class_template),
                joinedload(ClassInstance.academic_year),
            )
        )
        if teacher_id:
            stmt = stmt.join(ClassInstance.subject_schedules).where(
                ClassSubjectSchedule.teacher_id == teacher_id
            )
        if active_academic_year_only:
            stmt = stmt.where(AcademicYear.is_active.is_(True))

        stmt = stmt.order_by(
            AcademicYear.is_active.desc(),
            Class.grade.asc(),
            Class.name.asc(),
            AcademicYear.name.desc(),
        )
        return list(self.db.execute(stmt).unique().scalars().all())
