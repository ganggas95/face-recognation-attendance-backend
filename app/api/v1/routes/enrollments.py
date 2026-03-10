import uuid

from app.core.deps import (
    get_class_instance_repository,
    get_enrollment_repository,
    get_student_repository,
)
from app.core.exceptions import AppException
from app.models import StudentClassEnrollment
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.students import StudentRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.enrollments import EnrollmentCreate, EnrollmentRead
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.get("", response_model=ApiResponse)
def list_all(
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    student_ids: str | None = Query(default=None),
    active_academic_year_only: bool = Query(default=True),
) -> ApiResponse:
    parsed_student_ids: list[uuid.UUID] | None = None
    if student_ids:
        raw_parts = [p.strip() for p in student_ids.split(",") if p.strip()]
        try:
            parsed_student_ids = [uuid.UUID(p) for p in raw_parts]
        except ValueError:
            raise AppException(
                status_code=422,
                message="invalid student_ids",
                meta={"student_ids": student_ids},
            )

    items = enrollment_repo.list_by_student_ids(
        student_ids=parsed_student_ids,
        active_academic_year_only=active_academic_year_only,
    )
    payload_items = [
        EnrollmentRead.model_validate(item).model_dump() for item in items
    ]
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: EnrollmentCreate,
    student_repo: StudentRepository = Depends(get_student_repository),
    class_instance_repo: ClassInstanceRepository = Depends(
        get_class_instance_repository
    ),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
) -> ApiResponse:
    student = student_repo.get(payload.student_id)
    if not student:
        raise AppException(
            status_code=404,
            message="student not found",
            meta={"student_id": str(payload.student_id)},
        )

    class_instance = class_instance_repo.get(payload.class_instance_id)
    if not class_instance:
        raise AppException(
            status_code=404,
            message="class instance not found",
            meta={"class_instance_id": str(payload.class_instance_id)},
        )

    existing = enrollment_repo.get_by_student_class_instance(
        student_id=payload.student_id,
        class_instance_id=payload.class_instance_id,
    )
    if existing:
        raise AppException(
            status_code=409,
            message="student already enrolled",
            meta={
                "student_id": str(payload.student_id),
                "class_instance_id": str(payload.class_instance_id),
            },
        )

    enrollment = StudentClassEnrollment(
        student_id=payload.student_id,
        class_instance_id=payload.class_instance_id,
    )
    enrollment_repo.add(enrollment)
    enrollment_repo.db.commit()
    enrollment_repo.db.refresh(enrollment)

    item = EnrollmentRead.model_validate(enrollment).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )
