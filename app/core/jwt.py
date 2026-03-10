from datetime import datetime, timedelta

from app.core.config import settings
from app.core.exceptions import AppException
from jose import JWTError, jwt


def _create_token(
    *,
    subject: str,
    expires_minutes: int,
    token_type: str,
) -> str:
    if not settings.jwt_secret_key:
        raise AppException(
            status_code=500,
            message="JWT_SECRET_KEY env var is required",
            meta={},
        )
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire, "type": token_type}
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(*, subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_minutes=settings.access_token_expire_minutes,
        token_type="access",
    )


def create_refresh_token(*, subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_minutes=settings.refresh_token_expire_minutes,
        token_type="refresh",
    )


def _decode_token(token: str, *, expected_type: str) -> dict:
    if not settings.jwt_secret_key:
        raise AppException(
            status_code=500,
            message="JWT_SECRET_KEY env var is required",
            meta={},
        )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )
    if not isinstance(payload, dict) or not payload.get("sub"):
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )
    token_type = payload.get("type")
    if expected_type == "access" and token_type is None:
        return payload
    if token_type != expected_type:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )
    return payload


def decode_access_token(token: str) -> dict:
    return _decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict:
    return _decode_token(token, expected_type="refresh")
