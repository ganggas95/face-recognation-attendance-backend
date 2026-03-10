from app.core.deps import (get_class_instance_repository, get_current_user,
                           get_teacher_repository)
from app.models import User
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.api_response import ApiResponse, build_response
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


@router.get("/options", response_model=ApiResponse)
def list_options(
    repo: ClassInstanceRepository = Depends(get_class_instance_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    current_user: User = Depends(get_current_user),
    active_academic_year_only: bool = Query(default=True),
) -> ApiResponse:
    role = str(getattr(current_user, "role", "")).strip().upper()
    teacher_id = None
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
    if active_academic_year_only:
        ensure_fn = getattr(repo, "ensure_active_year_instances", None)
        if callable(ensure_fn):
            ensure_fn()
    items = repo.list_options(
        active_academic_year_only=active_academic_year_only,
        teacher_id=teacher_id,
    )
    payload_items = []
    for ci in items:
        cls = ci.class_template
        ay = ci.academic_year
        class_label = (
            f"Kelas {getattr(cls, 'grade', '-')}.{getattr(cls, 'name', '-')}"
            if cls
            else "-"
        )
        ay_label = getattr(ay, "name", "-")
        is_active = bool(getattr(ay, "is_active", False))
        active_part = " (Aktif)" if is_active else ""
        label = f"{class_label} — TA {ay_label}{active_part}"
        payload_items.append(
            {
                "id": str(ci.id),
                "label": label,
                "class_id": str(ci.class_id),
                "academic_year_id": str(ci.academic_year_id),
            }
        )

    return build_response(
        status=status.HTTP_200_OK,
        data={"items": payload_items},
        message="ok",
        meta={"count": len(payload_items)},
    )
