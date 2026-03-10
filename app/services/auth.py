import uuid

from app.core.exceptions import AppException
from app.core.jwt import (create_access_token, create_refresh_token,
                          decode_refresh_token)
from app.core.security import verify_password
from app.models import User
from app.repositories.users import UserRepository


def login(
    repo: UserRepository,
    *,
    email: str,
    password: str,
) -> tuple[str, str]:
    user: User | None = repo.get_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=401,
            message="invalid credentials",
            meta={},
        )
    if not user.is_active:
        raise AppException(
            status_code=403,
            message="user is inactive",
            meta={},
        )
    return (
        create_access_token(subject=str(user.id)),
        create_refresh_token(subject=str(user.id)),
    )


def refresh_tokens(
    repo: UserRepository,
    *,
    refresh_token: str,
) -> tuple[str, str]:
    payload = decode_refresh_token(refresh_token)
    subject = payload.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except ValueError:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )

    user = repo.get(user_id)
    if not user or not user.is_active:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )

    return (
        create_access_token(subject=str(user.id)),
        create_refresh_token(subject=str(user.id)),
    )
