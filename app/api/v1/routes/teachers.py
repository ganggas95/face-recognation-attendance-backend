from uuid import UUID

from app.core.deps import get_teacher_repository, get_user_repository
from app.repositories.teachers import TeacherRepository
from app.repositories.users import UserRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.schemas.teachers import TeacherCreate, TeacherRead, TeacherUpdate
from app.services.teachers import (
    create_teacher,
    delete_teacher,
    get_teacher,
    list_teachers,
    update_teacher,
)
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: TeacherCreate,
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> ApiResponse:
    teacher = create_teacher(teacher_repo, user_repo, payload)
    item = TeacherRead.model_validate(teacher).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: TeacherRepository = Depends(get_teacher_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_teachers(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    payload_items = [
        TeacherRead.model_validate(item).model_dump() for item in items
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


@router.get("/options", response_model=ApiResponse)
def list_options(
    repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    items = repo.list_options()
    payload_items = [
        {
            "id": str(t.id),
            "label": t.name,
            "user_id": str(t.user_id),
            "name": t.name,
            "nip": t.nip,
            "phone": t.phone,
        }
        for t in items
    ]
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )


@router.get("/{teacher_id}", response_model=ApiResponse)
def get_one(
    teacher_id: UUID,
    repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    teacher = get_teacher(repo, teacher_id)
    item = TeacherRead.model_validate(teacher).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.patch("/{teacher_id}", response_model=ApiResponse)
def update(
    teacher_id: UUID,
    payload: TeacherUpdate,
    repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    teacher = update_teacher(repo, teacher_id, payload)
    item = TeacherRead.model_validate(teacher).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.delete("/{teacher_id}", response_model=ApiResponse)
def delete(
    teacher_id: UUID,
    repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    delete_teacher(repo, teacher_id)
    return build_response(
        status=status.HTTP_200_OK,
        data={},
        message="deleted",
        meta={},
    )
