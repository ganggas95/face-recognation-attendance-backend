from uuid import UUID

from app.core.deps import (get_class_instance_repository,
                           get_class_subject_assignment_repository,
                           get_subject_repository, get_teacher_repository)
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.class_subject_assignments import \
    ClassSubjectAssignmentRepository
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.class_subject_assignments import (
    ClassSubjectAssignmentCreate, ClassSubjectAssignmentRead,
    ClassSubjectAssignmentUpdate)
from app.schemas.pagination import PaginationParams
from app.services.class_subject_assignments import (
    create_class_subject_assignment, delete_class_subject_assignment,
    list_class_subject_assignments, update_class_subject_assignment)
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: ClassSubjectAssignmentCreate,
    assignment_repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
    class_instance_repo: ClassInstanceRepository = Depends(
        get_class_instance_repository
    ),
    subject_repo: SubjectRepository = Depends(get_subject_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    assignment = create_class_subject_assignment(
        assignment_repo,
        class_instance_repo,
        subject_repo,
        teacher_repo,
        payload,
    )
    item = ClassSubjectAssignmentRead.model_validate(assignment).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    class_instance_id: UUID | None = Query(default=None),
    teacher_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_class_subject_assignments(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
        class_instance_id=class_instance_id,
        teacher_id=teacher_id,
        subject_id=subject_id,
    )
    payload_items = [
        ClassSubjectAssignmentRead.model_validate(item).model_dump()
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


@router.get("/options", response_model=ApiResponse)
def list_options(
    repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
    active_academic_year_only: bool = Query(default=True),
) -> ApiResponse:
    items = repo.list_options(
        active_academic_year_only=active_academic_year_only,
    )
    payload_items = []
    for a in items:
        ci = a.class_instance
        cls = ci.class_template if ci else None
        ay = ci.academic_year if ci else None
        class_label = (
            f"Kelas {getattr(cls, 'grade', '-')}.{getattr(cls, 'name', '-')}"
            if cls
            else "-"
        )
        ay_label = getattr(ay, "name", "-")
        subject_label = getattr(a.subject, "name", "-")
        teacher_label = getattr(a.teacher, "name", "-")
        label = (
            f"{class_label} ({ay_label}) · {subject_label} · {teacher_label}"
        )
        payload_items.append(
            {
                "id": str(a.id),
                "label": label,
                "class_instance_id": str(a.class_instance_id),
                "subject_id": str(a.subject_id),
                "teacher_id": str(a.teacher_id),
            }
        )

    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )


@router.patch("/{assignment_id}", response_model=ApiResponse)
def update(
    assignment_id: UUID,
    payload: ClassSubjectAssignmentUpdate,
    assignment_repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ApiResponse:
    assignment = update_class_subject_assignment(
        assignment_repo,
        teacher_repo,
        assignment_id,
        payload,
    )
    item = ClassSubjectAssignmentRead.model_validate(assignment).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.delete("/{assignment_id}", response_model=ApiResponse)
def delete(
    assignment_id: UUID,
    repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
) -> ApiResponse:
    delete_class_subject_assignment(repo, assignment_id)
    return build_response(
        status=status.HTTP_200_OK,
        data={},
        message="deleted",
        meta={},
    )
