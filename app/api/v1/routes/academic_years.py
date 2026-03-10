from uuid import UUID

from app.core.deps import get_academic_year_repository
from app.repositories.academic_years import AcademicYearRepository
from app.schemas.academic_years import AcademicYearCreate, AcademicYearRead
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.services.academic_years import (activate_academic_year,
                                         create_academic_year,
                                         list_academic_years)
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: AcademicYearCreate,
    repo: AcademicYearRepository = Depends(get_academic_year_repository),
) -> ApiResponse:
    academic_year = create_academic_year(repo, payload)
    item = AcademicYearRead.model_validate(academic_year).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: AcademicYearRepository = Depends(get_academic_year_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_academic_years(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    payload_items = [
        AcademicYearRead.model_validate(item).model_dump()
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


@router.post("/{academic_year_id}/activate", response_model=ApiResponse)
def activate(
    academic_year_id: UUID,
    repo: AcademicYearRepository = Depends(get_academic_year_repository),
) -> ApiResponse:
    academic_year = activate_academic_year(repo, academic_year_id)
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="academic year not found",
        )
    item = AcademicYearRead.model_validate(academic_year).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )
