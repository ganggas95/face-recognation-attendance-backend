from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models import Teacher, User
from app.repositories.teachers import TeacherRepository
from app.repositories.users import UserRepository
from app.schemas.teachers import TeacherCreate, TeacherUpdate
from sqlalchemy.exc import IntegrityError


def create_teacher(
    teacher_repo: TeacherRepository,
    user_repo: UserRepository,
    payload: TeacherCreate,
) -> Teacher:
    existing_user = user_repo.get_by_email(payload.user.email)
    if existing_user:
        raise AppException(
            status_code=409,
            message="user already exists",
            meta={"email": payload.user.email},
        )

    user = User(
        email=payload.user.email,
        password_hash=hash_password(payload.user.password),
        role="TEACHER",
        is_active=payload.user.is_active,
    )
    user_repo.add(user)
    teacher_repo.db.flush()

    teacher = Teacher(
        user_id=user.id,
        name=payload.name,
        nip=payload.nip,
        phone=payload.phone,
    )
    teacher_repo.add(teacher)
    try:
        teacher_repo.db.commit()
    except IntegrityError:
        teacher_repo.db.rollback()
        raise AppException(
            status_code=409,
            message="conflict",
            meta={},
        )
    teacher_repo.db.refresh(teacher)
    return teacher


def get_teacher(repo: TeacherRepository, teacher_id) -> Teacher:
    teacher = repo.get(teacher_id)
    if not teacher:
        raise AppException(
            status_code=404,
            message="teacher not found",
            meta={"teacher_id": str(teacher_id)},
        )
    return teacher


def update_teacher(
    repo: TeacherRepository,
    teacher_id,
    payload: TeacherUpdate,
) -> Teacher:
    teacher = get_teacher(repo, teacher_id)
    if payload.name is not None:
        teacher.name = payload.name
    if payload.nip is not None:
        teacher.nip = payload.nip
    if payload.phone is not None:
        teacher.phone = payload.phone
    repo.db.commit()
    repo.db.refresh(teacher)
    return teacher


def delete_teacher(repo: TeacherRepository, teacher_id) -> None:
    teacher = get_teacher(repo, teacher_id)
    repo.delete(teacher)
    try:
        repo.db.commit()
    except IntegrityError:
        repo.db.rollback()
        raise AppException(
            status_code=409,
            message="teacher is referenced",
            meta={"teacher_id": str(teacher_id)},
        )


def list_teachers(
    repo: TeacherRepository,
    *,
    offset: int,
    limit: int,
) -> tuple[list[Teacher], int]:
    return repo.list_paginated(offset=offset, limit=limit)
