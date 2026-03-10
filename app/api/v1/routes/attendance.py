import uuid
from datetime import date as dt_date

from app.core.deps import (get_attendance_repository,
                           get_class_subject_schedule_repository,
                           get_current_user, get_enrollment_repository,
                           get_student_face_repository, get_student_repository,
                           get_teacher_repository)
from app.core.exceptions import AppException
from app.models import User
from app.repositories.attendances import AttendanceRepository
from app.repositories.class_subject_schedules import \
    ClassSubjectScheduleRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.services.attendance import (list_attendance_records,
                                     verify_attendance_by_face)
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

router = APIRouter()


@router.get("", response_model=ApiResponse)
def list_all(
    repo: AttendanceRepository = Depends(get_attendance_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    class_instance_id: uuid.UUID | None = Query(default=None),
    subject_id: uuid.UUID | None = Query(default=None),
    date: dt_date | None = Query(default=None),
    q: str | None = Query(default=None),
) -> ApiResponse:
    role = str(getattr(current_user, "role", "")).strip().upper()
    teacher_id: uuid.UUID | None = None
    if role == "TEACHER":
        teacher = teacher_repo.get_by_user_id(current_user.id)
        if not teacher:
            return build_response(
                status=status.HTTP_200_OK,
                data={"items": []},
                message="ok",
                meta={
                    "count": 0,
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                },
            )
        teacher_id = teacher.id

    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_attendance_records(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
        class_instance_id=class_instance_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        date=date,
        student_name=q,
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
    schedule_id: uuid.UUID = Form(...),
    image: UploadFile = File(...),
    schedule_repo: ClassSubjectScheduleRepository = Depends(
        get_class_subject_schedule_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    face_repo: StudentFaceRepository = Depends(get_student_face_repository),
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    student_repo: StudentRepository = Depends(get_student_repository),
) -> ApiResponse:
    role = str(getattr(current_user, "role", "")).strip().upper()
    if role == "TEACHER":
        teacher = teacher_repo.get_by_user_id(current_user.id)
        schedule = schedule_repo.get(schedule_id)
        if not teacher or not schedule or schedule.teacher_id != teacher.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="forbidden",
                meta={},
            )

    result = verify_attendance_by_face(
        schedule_repo=schedule_repo,
        enrollment_repo=enrollment_repo,
        face_repo=face_repo,
        attendance_repo=attendance_repo,
        student_repo=student_repo,
        schedule_id=schedule_id,
        image_bytes=await image.read(),
    )
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": result},
        message="ok",
        meta={},
    )
