from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate, UserUpdate
from sqlalchemy.exc import IntegrityError


def create_user(repo: UserRepository, payload: UserCreate) -> User:
    existing = repo.get_by_email(payload.email)
    if existing:
        raise AppException(
            status_code=409,
            message="user already exists",
            meta={"email": payload.email},
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role.strip().upper(),
        is_active=payload.is_active,
    )
    repo.add(user)
    repo.db.commit()
    repo.db.refresh(user)
    return user


def get_user(repo: UserRepository, user_id) -> User:
    user = repo.get(user_id)
    if not user:
        raise AppException(
            status_code=404,
            message="user not found",
            meta={"user_id": str(user_id)},
        )
    return user


def update_user(
    repo: UserRepository,
    user_id,
    payload: UserUpdate,
) -> User:
    user = get_user(repo, user_id)

    if payload.email is not None:
        email = payload.email.strip()
        if not email:
            raise AppException(
                status_code=422,
                message="invalid email",
                meta={},
            )
        existing = repo.get_by_email(email)
        if existing and existing.id != user.id:
            raise AppException(
                status_code=409,
                message="user already exists",
                meta={"email": email},
            )
        user.email = email

    if payload.password is not None:
        if not payload.password:
            raise AppException(
                status_code=422,
                message="invalid password",
                meta={},
            )
        user.password_hash = hash_password(payload.password)

    if payload.role is not None:
        role = payload.role.strip().upper()
        if not role:
            raise AppException(
                status_code=422,
                message="invalid role",
                meta={},
            )
        user.role = role

    if payload.is_active is not None:
        user.is_active = payload.is_active

    try:
        repo.db.commit()
    except IntegrityError:
        repo.db.rollback()
        raise AppException(
            status_code=409,
            message="conflict",
            meta={},
        )
    repo.db.refresh(user)
    return user


def delete_user(repo: UserRepository, user_id) -> None:
    user = get_user(repo, user_id)
    repo.delete(user)
    try:
        repo.db.commit()
    except IntegrityError:
        repo.db.rollback()
        raise AppException(
            status_code=409,
            message="user is referenced",
            meta={"user_id": str(user_id)},
        )


def list_users(
    repo: UserRepository,
    *,
    offset: int,
    limit: int,
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    return repo.list_paginated(
        offset=offset,
        limit=limit,
        q=q,
        role=role.strip().upper() if role else None,
        is_active=is_active,
    )
