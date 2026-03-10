import uuid

from app.core.exceptions import AppException
from app.models import Subject
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.subjects import SubjectCreate


def create_subject(
    subject_repo: SubjectRepository,
    teacher_repo: TeacherRepository,
    payload: SubjectCreate,
) -> Subject:
    if payload.teacher_id is not None:
        teacher = teacher_repo.get(payload.teacher_id)
        if not teacher:
            raise AppException(
                status_code=404,
                message="teacher not found",
                meta={"teacher_id": str(payload.teacher_id)},
            )
    subject = Subject(
        code=payload.code,
        name=payload.name,
        teacher_id=payload.teacher_id,
    )
    subject_repo.add(subject)
    subject_repo.db.commit()
    subject_repo.db.refresh(subject)
    return subject


def list_subjects(
    repo: SubjectRepository,
    *,
    offset: int,
    limit: int,
    teacher_id: uuid.UUID | None = None,
) -> tuple[list[Subject], int]:
    return repo.list_paginated(
        offset=offset,
        limit=limit,
        teacher_id=teacher_id,
    )
