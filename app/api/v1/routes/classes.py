from uuid import UUID

from app.core.deps import (
    get_academic_year_repository,
    get_class_instance_repository,
    get_class_repository,
    get_teacher_repository,
)
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.classes import ClassRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.classes import ClassCreate, ClassRead, ClassUpdate
from app.schemas.pagination import PaginationParams
from app.services.classes import (
    create_class,
    delete_class,
    get_class,
    list_classes,
    update_class,
)
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: ClassCreate,
    repo: ClassRepository = Depends(get_class_repository),
    class_instance_repo: ClassInstanceRepository = Depends(
        get_class_instance_repository
    ),
    academic_year_repo: AcademicYearRepository = Depends(
        get_academic_year_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    class_template = create_class(
        repo,
        class_instance_repo,
        academic_year_repo,
        teacher_repo,
        payload,
    )
    item = ClassRead.model_validate(class_template).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: ClassRepository = Depends(get_class_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_classes(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    payload_items = [
        ClassRead.model_validate(item).model_dump()
        for item in items
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


@router.get("/{class_id}", response_model=ApiResponse)
def get_one(
    class_id: UUID,
    repo: ClassRepository = Depends(get_class_repository),
) -> ApiResponse:
    class_template = get_class(repo, class_id)
    item = ClassRead.model_validate(class_template).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.patch("/{class_id}", response_model=ApiResponse)
def update(
    class_id: UUID,
    payload: ClassUpdate,
    repo: ClassRepository = Depends(get_class_repository),
    class_instance_repo: ClassInstanceRepository = Depends(
        get_class_instance_repository
    ),
    academic_year_repo: AcademicYearRepository = Depends(
        get_academic_year_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    class_template = update_class(
        repo,
        teacher_repo,
        class_instance_repo,
        academic_year_repo,
        class_id,
        payload,
    )
    item = ClassRead.model_validate(class_template).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.delete("/{class_id}", response_model=ApiResponse)
def delete(
    class_id: UUID,
    repo: ClassRepository = Depends(get_class_repository),
) -> ApiResponse:
    delete_class(repo, class_id)
    return build_response(
        status=status.HTTP_200_OK,
        data={},
        message="deleted",
        meta={},
    )
