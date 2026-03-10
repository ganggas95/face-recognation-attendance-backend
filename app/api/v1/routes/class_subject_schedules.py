from uuid import UUID

from app.core.deps import (get_class_instance_repository,
                           get_class_subject_assignment_repository,
                           get_class_subject_schedule_repository,
                           get_current_user, get_subject_repository,
                           get_teacher_repository)
from app.models import User
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.class_subject_assignments import \
    ClassSubjectAssignmentRepository
from app.repositories.class_subject_schedules import \
    ClassSubjectScheduleRepository
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.class_subject_schedules import (ClassSubjectScheduleCreate,
                                                 ClassSubjectScheduleRead)
from app.schemas.pagination import PaginationParams
from app.services.class_subject_schedules import (
    create_class_subject_schedule, list_class_subject_schedules)
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: ClassSubjectScheduleCreate,
    schedule_repo: ClassSubjectScheduleRepository = Depends(
        get_class_subject_schedule_repository
    ),
    class_instance_repo: ClassInstanceRepository = Depends(
        get_class_instance_repository
    ),
    subject_repo: SubjectRepository = Depends(get_subject_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    assignment_repo: ClassSubjectAssignmentRepository = Depends(
        get_class_subject_assignment_repository
    ),
) -> ApiResponse:
    schedule = create_class_subject_schedule(
        schedule_repo,
        class_instance_repo,
        subject_repo,
        teacher_repo,
        assignment_repo,
        payload,
    )
    item = ClassSubjectScheduleRead.model_validate(schedule).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: ClassSubjectScheduleRepository = Depends(
        get_class_subject_schedule_repository
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    class_instance_id: UUID | None = Query(default=None),
    teacher_id: UUID | None = Query(default=None),
    day_of_week: int | None = Query(default=None, ge=0, le=6),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    items, total = list_class_subject_schedules(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
        class_instance_id=class_instance_id,
        teacher_id=teacher_id,
        day_of_week=day_of_week,
    )
    payload_items = [
        ClassSubjectScheduleRead.model_validate(item).model_dump()
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
    repo: ClassSubjectScheduleRepository = Depends(
        get_class_subject_schedule_repository
    ),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
    active_academic_year_only: bool = Query(default=True),
) -> ApiResponse:
    day_labels = {
        0: "Minggu",
        1: "Senin",
        2: "Selasa",
        3: "Rabu",
        4: "Kamis",
        5: "Jumat",
        6: "Sabtu",
    }

    role = str(getattr(current_user, "role", "")).strip().upper()
    teacher_id: UUID | None = None
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
        teacher_id = teacher.id

    items = repo.list_options(
        active_academic_year_only=active_academic_year_only,
        teacher_id=teacher_id,
    )
    payload_items = []
    for s in items:
        ci = s.class_instance
        cls = ci.class_template if ci else None
        ay = ci.academic_year if ci else None
        class_label = (
            f"Kelas {getattr(cls, 'grade', '-')}.{getattr(cls, 'name', '-')}"
            if cls
            else "-"
        )
        ay_label = getattr(ay, "name", "-")
        subject_label = getattr(s.subject, "name", "-")
        teacher_label = getattr(s.teacher, "name", "-")
        day_label = day_labels.get(getattr(s, "day_of_week", -1), "-")
        start_time = getattr(s, "start_time", None)
        end_time = getattr(s, "end_time", None)
        start_label = start_time.strftime("%H:%M") if start_time else "-"
        end_label = end_time.strftime("%H:%M") if end_time else "-"
        room_label = getattr(s, "room", None)
        room_part = f" · {room_label}" if room_label else ""
        label = (
            f"{day_label} {start_label}-{end_label} · "
            f"{class_label} ({ay_label}) · {subject_label} · "
            f"{teacher_label}{room_part}"
        )

        payload_items.append(
            {
                "id": str(s.id),
                "label": label,
                "class_instance_id": str(s.class_instance_id),
                "subject_id": str(s.subject_id),
                "teacher_id": str(s.teacher_id),
                "class_subject_assignment_id": (
                    str(s.class_subject_assignment_id)
                    if s.class_subject_assignment_id
                    else None
                ),
                "day_of_week": s.day_of_week,
                "start_time": (
                    s.start_time.isoformat()
                    if getattr(s, "start_time", None)
                    else None
                ),
                "end_time": (
                    end_time.isoformat() if end_time else None
                ),
                "room": s.room,
            }
        )

    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )
