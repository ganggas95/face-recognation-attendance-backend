from uuid import UUID

from app.core.deps import (get_current_user, get_subject_repository,
                           get_teacher_repository)
from app.models import User
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.schemas.subjects import SubjectCreate, SubjectRead
from app.services.subjects import create_subject, list_subjects
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: SubjectCreate,
    subject_repo: SubjectRepository = Depends(get_subject_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    subject = create_subject(subject_repo, teacher_repo, payload)
    item = SubjectRead.model_validate(subject).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: SubjectRepository = Depends(get_subject_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    teacher_id: UUID | None = Query(default=None),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_subjects(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
        teacher_id=teacher_id,
    )
    payload_items = [
        SubjectRead.model_validate(item).model_dump() for item in items
    ]
    print(payload_items)
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
    repo: SubjectRepository = Depends(get_subject_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    role = str(getattr(current_user, "role", "")).strip().upper()
    if role == "TEACHER":
        teacher = teacher_repo.get_by_user_id(current_user.id)
        if not teacher:
            items = []
            return build_response(
                status=status.HTTP_200_OK,
                data={"items": items},
                message="ok",
                meta={"count": 0},
            )
        items = repo.list_options_by_teacher_id(teacher_id=teacher.id)
    else:
        items = repo.list_options()
    payload_items = []
    for s in items:
        label = f"{s.code} · {s.name}" if s.code else s.name
        payload_items.append(
            {
                "id": str(s.id),
                "label": label,
                "code": s.code,
                "name": s.name,
                "teacher_id": str(s.teacher_id) if s.teacher_id else None,
            }
        )
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )
