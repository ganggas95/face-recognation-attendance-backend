from uuid import UUID

from app.core.deps import get_user_repository, require_roles
from app.core.exceptions import AppException
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.services.users import (create_user, delete_user, get_user, list_users,
                                update_user)
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: UserCreate,
    repo: UserRepository = Depends(get_user_repository),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    user = create_user(repo, payload)
    item = UserRead.model_validate(user).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: UserRepository = Depends(get_user_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_users(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
        q=q,
        role=role,
        is_active=is_active,
    )
    payload_items = [
        UserRead.model_validate(item).model_dump() for item in items
    ]
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={
            "count": len(payload_items),
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
        },
    )


@router.get("/{user_id}", response_model=ApiResponse)
def get_one(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repository),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    user = get_user(repo, user_id)
    item = UserRead.model_validate(user).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.patch("/{user_id}", response_model=ApiResponse)
def update(
    user_id: UUID,
    payload: UserUpdate,
    repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    if payload.is_active is False and user_id == current_user.id:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            message="cannot deactivate self",
            meta={"user_id": str(user_id)},
        )
    user = update_user(repo, user_id, payload)
    item = UserRead.model_validate(user).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.post("/{user_id}/activate", response_model=ApiResponse)
def activate(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repository),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    user = update_user(repo, user_id, UserUpdate(is_active=True))
    item = UserRead.model_validate(user).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.post("/{user_id}/deactivate", response_model=ApiResponse)
def deactivate(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    if user_id == current_user.id:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            message="cannot deactivate self",
            meta={"user_id": str(user_id)},
        )
    user = update_user(repo, user_id, UserUpdate(is_active=False))
    item = UserRead.model_validate(user).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.delete("/{user_id}", response_model=ApiResponse)
def delete(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    if user_id == current_user.id:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            message="cannot delete self",
            meta={"user_id": str(user_id)},
        )
    delete_user(repo, user_id)
    return build_response(
        status=status.HTTP_200_OK,
        data={},
        message="deleted",
        meta={},
    )
