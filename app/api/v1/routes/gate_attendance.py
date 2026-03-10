import uuid
from datetime import date as dt_date
from datetime import time as dt_time

from app.core.deps import (get_academic_year_repository,
                           get_enrollment_repository,
                           get_gate_attendance_repository,
                           get_school_setting_repository,
                           get_student_attendance_repository,
                           get_student_face_repository, get_student_repository,
                           require_roles)
from app.models import User
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.gate_attendances import GateAttendanceRepository
from app.repositories.school_settings import SchoolSettingRepository
from app.repositories.student_attendances import StudentAttendanceRepository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.services.gate_attendance import (list_gate_attendance_records,
                                          verify_gate_attendance_by_face)
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

router = APIRouter()


def _default_gate_in_time() -> dt_time:
    return dt_time(hour=7, minute=0, second=0)


def _default_gate_out_time() -> dt_time:
    return dt_time(hour=15, minute=0, second=0)


def _get_gate_in_time(repo: SchoolSettingRepository) -> dt_time:
    settings = repo.get_default()
    if settings is None:
        settings = repo.upsert_default(
            gate_in_time=_default_gate_in_time(),
            gate_out_time=_default_gate_out_time(),
        )
        repo.db.commit()
        repo.db.refresh(settings)
    value = getattr(settings, "gate_in_time", None)
    if getattr(value, "isoformat", None):
        return value.replace(microsecond=0, tzinfo=None)
    return _default_gate_in_time()


@router.get("", response_model=ApiResponse)
def list_all(
    repo: GateAttendanceRepository = Depends(get_gate_attendance_repository),
    school_setting_repo: SchoolSettingRepository = Depends(
        get_school_setting_repository
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    date: dt_date | None = Query(default=None),
    direction: str | None = Query(default=None),
    q: str | None = Query(default=None),
    recorded_by_user_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_gate_attendance_records(
        repo,
        gate_in_time=_get_gate_in_time(school_setting_repo),
        offset=pagination.offset,
        limit=pagination.page_size,
        date=date,
        direction=direction,
        student_name=q,
        recorded_by_user_id=recorded_by_user_id,
    )
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": items},
        message="ok",
        meta={
            "count": len(items),
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
        },
    )


@router.post("/verify", response_model=ApiResponse)
async def verify(
    direction: str = Form(...),
    image: UploadFile = File(...),
    academic_year_repo: AcademicYearRepository = Depends(
        get_academic_year_repository
    ),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    face_repo: StudentFaceRepository = Depends(get_student_face_repository),
    gate_attendance_repo: GateAttendanceRepository = Depends(
        get_gate_attendance_repository
    ),
    student_attendance_repo: StudentAttendanceRepository = Depends(
        get_student_attendance_repository
    ),
    school_setting_repo: SchoolSettingRepository = Depends(
        get_school_setting_repository
    ),
    student_repo: StudentRepository = Depends(get_student_repository),
    current_user: User = Depends(require_roles("ADMIN", "SECURITY")),
) -> ApiResponse:
    result = verify_gate_attendance_by_face(
        academic_year_repo=academic_year_repo,
        enrollment_repo=enrollment_repo,
        face_repo=face_repo,
        gate_attendance_repo=gate_attendance_repo,
        student_attendance_repo=student_attendance_repo,
        student_repo=student_repo,
        recorded_by_user_id=current_user.id,
        direction=direction,
        gate_in_time=_get_gate_in_time(school_setting_repo),
        image_bytes=await image.read(),
    )
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": result},
        message="ok",
        meta={},
    )
