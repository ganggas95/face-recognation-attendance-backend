import uuid

from app.core.exceptions import AppException
from app.models import Class, ClassInstance
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.classes import ClassRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.classes import ClassCreate, ClassUpdate
from sqlalchemy.exc import IntegrityError


def create_class(
    repo: ClassRepository,
    class_instance_repo: ClassInstanceRepository,
    academic_year_repo: AcademicYearRepository,
    teacher_repo: TeacherRepository,
    payload: ClassCreate,
) -> Class:
    if payload.homeroom_teacher_id:
        teacher = teacher_repo.get(payload.homeroom_teacher_id)
        if not teacher:
            raise AppException(
                status_code=404,
                message="teacher not found",
                meta={"teacher_id": str(payload.homeroom_teacher_id)},
            )
    class_template = Class(
        name=payload.name,
        grade=payload.grade,
        homeroom_teacher_id=payload.homeroom_teacher_id,
    )
    repo.add(class_template)
    repo.db.flush()

    target_year = None
    if payload.academic_year_id:
        target_year = academic_year_repo.get(payload.academic_year_id)
        if not target_year:
            raise AppException(
                status_code=404,
                message="academic year not found",
                meta={"academic_year_id": str(payload.academic_year_id)},
            )
    else:
        target_year = academic_year_repo.get_active()

    if target_year:
        existing_instance = class_instance_repo.get_by_class_academic_year(
            class_id=class_template.id,
            academic_year_id=target_year.id,
        )
        if not existing_instance:
            class_instance_repo.add(
                ClassInstance(
                    class_id=class_template.id,
                    academic_year_id=target_year.id,
                )
            )

    repo.db.commit()
    repo.db.refresh(class_template)
    return class_template


def get_class(repo: ClassRepository, class_id: uuid.UUID) -> Class:
    class_template = repo.get(class_id)
    if not class_template:
        raise AppException(
            status_code=404,
            message="class not found",
            meta={"class_id": str(class_id)},
        )
    return class_template


def update_class(
    repo: ClassRepository,
    teacher_repo: TeacherRepository,
    class_instance_repo: ClassInstanceRepository,
    academic_year_repo: AcademicYearRepository,
    class_id: uuid.UUID,
    payload: ClassUpdate,
) -> Class:
    class_template = get_class(repo, class_id)

    if payload.homeroom_teacher_id is not None:
        if payload.homeroom_teacher_id:
            teacher = teacher_repo.get(payload.homeroom_teacher_id)
            if not teacher:
                raise AppException(
                    status_code=404,
                    message="teacher not found",
                    meta={"teacher_id": str(payload.homeroom_teacher_id)},
                )
        class_template.homeroom_teacher_id = payload.homeroom_teacher_id

    if payload.name is not None:
        class_template.name = payload.name
    if payload.grade is not None:
        class_template.grade = payload.grade

    if payload.academic_year_id:
        academic_year = academic_year_repo.get(payload.academic_year_id)
        if not academic_year:
            raise AppException(
                status_code=404,
                message="academic year not found",
                meta={"academic_year_id": str(payload.academic_year_id)},
            )
        existing_instance = class_instance_repo.get_by_class_academic_year(
            class_id=class_template.id,
            academic_year_id=academic_year.id,
        )
        if not existing_instance:
            class_instance_repo.add(
                ClassInstance(
                    class_id=class_template.id,
                    academic_year_id=academic_year.id,
                )
            )

    repo.db.commit()
    repo.db.refresh(class_template)
    return class_template


def delete_class(repo: ClassRepository, class_id: uuid.UUID) -> None:
    class_template = get_class(repo, class_id)
    repo.delete(class_template)
    try:
        repo.db.commit()
    except IntegrityError:
        repo.db.rollback()
        raise AppException(
            status_code=409,
            message="class is referenced",
            meta={"class_id": str(class_id)},
        )


def list_classes(
    repo: ClassRepository,
    *,
    offset: int,
    limit: int,
) -> tuple[list[Class], int]:
    return repo.list_paginated(offset=offset, limit=limit)
