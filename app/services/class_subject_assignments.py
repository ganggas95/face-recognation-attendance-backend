import uuid

from app.core.exceptions import AppException
from app.models import ClassSubjectAssignment
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.class_subject_assignments import (
    ClassSubjectAssignmentRepository,
)
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.class_subject_assignments import (
    ClassSubjectAssignmentCreate,
    ClassSubjectAssignmentUpdate,
)


def create_class_subject_assignment(
    assignment_repo: ClassSubjectAssignmentRepository,
    class_instance_repo: ClassInstanceRepository,
    subject_repo: SubjectRepository,
    teacher_repo: TeacherRepository,
    payload: ClassSubjectAssignmentCreate,
) -> ClassSubjectAssignment:
    class_instance = class_instance_repo.get(payload.class_instance_id)
    if not class_instance:
        raise AppException(
            status_code=404,
            message="class instance not found",
            meta={"class_instance_id": str(payload.class_instance_id)},
        )

    subject = subject_repo.get(payload.subject_id)
    if not subject:
        raise AppException(
            status_code=404,
            message="subject not found",
            meta={"subject_id": str(payload.subject_id)},
        )

    teacher = teacher_repo.get(payload.teacher_id)
    if not teacher:
        raise AppException(
            status_code=404,
            message="teacher not found",
            meta={"teacher_id": str(payload.teacher_id)},
        )

    existing = assignment_repo.get_by_class_instance_subject(
        class_instance_id=payload.class_instance_id,
        subject_id=payload.subject_id,
    )
    if existing:
        raise AppException(
            status_code=409,
            message="assignment already exists",
            meta={
                "class_instance_id": str(payload.class_instance_id),
                "subject_id": str(payload.subject_id),
            },
        )

    assignment = ClassSubjectAssignment(
        class_instance_id=payload.class_instance_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
    )
    assignment_repo.add(assignment)
    assignment_repo.db.commit()
    assignment_repo.db.refresh(assignment)
    return assignment


def update_class_subject_assignment(
    assignment_repo: ClassSubjectAssignmentRepository,
    teacher_repo: TeacherRepository,
    assignment_id: uuid.UUID,
    payload: ClassSubjectAssignmentUpdate,
) -> ClassSubjectAssignment:
    assignment = assignment_repo.get(assignment_id)
    if not assignment:
        raise AppException(
            status_code=404,
            message="assignment not found",
            meta={"assignment_id": str(assignment_id)},
        )

    teacher = teacher_repo.get(payload.teacher_id)
    if not teacher:
        raise AppException(
            status_code=404,
            message="teacher not found",
            meta={"teacher_id": str(payload.teacher_id)},
        )

    assignment.teacher_id = payload.teacher_id
    assignment_repo.db.commit()
    assignment_repo.db.refresh(assignment)
    return assignment


def delete_class_subject_assignment(
    assignment_repo: ClassSubjectAssignmentRepository,
    assignment_id: uuid.UUID,
) -> None:
    assignment = assignment_repo.get(assignment_id)
    if not assignment:
        raise AppException(
            status_code=404,
            message="assignment not found",
            meta={"assignment_id": str(assignment_id)},
        )
    assignment_repo.delete(assignment)
    assignment_repo.db.commit()


def list_class_subject_assignments(
    repo: ClassSubjectAssignmentRepository,
    *,
    offset: int,
    limit: int,
    class_instance_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
) -> tuple[list[ClassSubjectAssignment], int]:
    return repo.list_paginated(
        offset=offset,
        limit=limit,
        class_instance_id=class_instance_id,
        teacher_id=teacher_id,
        subject_id=subject_id,
    )
