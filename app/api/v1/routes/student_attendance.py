import os
import uuid
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path

from app.core.exceptions import AppException
from app.core.deps import (get_school_setting_repository,
                           get_student_attendance_repository, require_roles)
from app.models import User
from app.models.student_attendances import StudentAttendance
from app.repositories.school_settings import SchoolSettingRepository
from app.repositories.student_attendances import StudentAttendanceRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.schemas.student_attendance import (StudentAttendanceLeaveCreate,
                                            StudentAttendanceListItem)
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, select

router = APIRouter()


def _default_gate_in_time() -> dt_time:
    return dt_time(hour=7, minute=0, second=0)


def _default_gate_out_time() -> dt_time:
    return dt_time(hour=15, minute=0, second=0)


def _normalize_time(value: dt_time | None, fallback: dt_time) -> dt_time:
    if value is None:
        return fallback
    if getattr(value, "isoformat", None):
        return value.replace(microsecond=0, tzinfo=None)
    return fallback


def _get_gate_times(repo: SchoolSettingRepository) -> tuple[dt_time, dt_time]:
    settings = repo.get_default()
    if settings is None:
        settings = repo.upsert_default(
            gate_in_time=_default_gate_in_time(),
            gate_out_time=_default_gate_out_time(),
        )
        repo.db.commit()
        repo.db.refresh(settings)
    gate_in_time = _normalize_time(
        getattr(settings, "gate_in_time", None),
        _default_gate_in_time(),
    )
    gate_out_time = _normalize_time(
        getattr(settings, "gate_out_time", None),
        _default_gate_out_time(),
    )
    return gate_in_time, gate_out_time


def _evidence_dir() -> Path:
    base = os.getenv(
        "STUDENT_ATTENDANCE_EVIDENCE_DIR",
        "storage/student-attendance-evidence",
    )
    return Path(base)


def _evidence_path(attendance_id: uuid.UUID, filename: str) -> Path:
    ext = Path(filename).suffix.lower().strip()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    return _evidence_dir() / f"{attendance_id}{ext}"


def _should_mark_bolos(
    *,
    today: dt_date,
    now_time: dt_time,
    row_date: dt_date,
    gate_out_time: dt_time,
) -> bool:
    if row_date < today:
        return True
    if row_date > today:
        return False
    return now_time >= gate_out_time


@router.get("", response_model=ApiResponse)
def list_all(
    repo: StudentAttendanceRepository = Depends(
        get_student_attendance_repository
    ),
    school_setting_repo: SchoolSettingRepository = Depends(
        get_school_setting_repository
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    date_from: dt_date | None = Query(default=None),
    date_to: dt_date | None = Query(default=None),
    class_instance_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    _: User = Depends(require_roles("ADMIN", "TEACHER")),
) -> ApiResponse:
    today = dt_date.today()
    start = date_from or today
    end = date_to or start
    if end < start:
        start, end = end, start

    gate_in_time, gate_out_time = _get_gate_times(school_setting_repo)
    from app.models.academic_years import AcademicYear
    from app.models.class_instances import ClassInstance
    from app.models.enrollments import StudentClassEnrollment
    from app.models.students import Student

    active_student_ids = list(
        repo.db.execute(
            select(Student.id)
            .join(
                StudentClassEnrollment,
                StudentClassEnrollment.student_id == Student.id,
            )
            .join(
                ClassInstance,
                ClassInstance.id == StudentClassEnrollment.class_instance_id,
            )
            .join(
                AcademicYear,
                AcademicYear.id == ClassInstance.academic_year_id,
            )
            .where(AcademicYear.is_active.is_(True))
            .distinct()
        ).scalars()
    )
    student_ids = active_student_ids
    if not student_ids:
        student_ids = list(repo.db.execute(select(Student.id)).scalars())

    d = start
    while d <= end:
        existing_ids = set(
            repo.db.execute(
                select(StudentAttendance.student_id).where(
                    StudentAttendance.date == d,
                    StudentAttendance.student_id.in_(student_ids),
                )
            ).scalars()
        )
        missing = [sid for sid in student_ids if sid not in existing_ids]
        if missing:
            repo.db.add_all(
                [
                    StudentAttendance(
                        student_id=sid,
                        date=d,
                        status="TANPA_KETERANGAN",
                        verified=False,
                        verified_at=None,
                        verified_by=None,
                    )
                    for sid in missing
                ]
            )
            repo.db.flush()
        d = dt_date.fromordinal(d.toordinal() + 1)

    repo.backfill_from_gate_attendance(
        date_from=start,
        date_to=end,
        gate_in_time=gate_in_time,
    )
    repo.db.commit()

    pagination = PaginationParams(page=page, page_size=page_size)

    from app.models.classes import Class
    from app.models.gate_attendances import GateAttendance
    from app.models.users import User as UserModel

    checkin = GateAttendance.__table__.alias("checkin")
    checkout = GateAttendance.__table__.alias("checkout")

    stmt = (
        select(
            StudentAttendance,
            Student.name.label("student_name"),
            Student.nis.label("student_nis"),
            Class.name.label("class_name"),
            checkin.c.time.label("checkin_time"),
            checkout.c.time.label("checkout_time"),
            UserModel.email.label("verified_by_email"),
        )
        .join(Student, Student.id == StudentAttendance.student_id)
        .outerjoin(
            StudentClassEnrollment,
            StudentClassEnrollment.student_id == Student.id,
        )
        .outerjoin(
            ClassInstance,
            ClassInstance.id == StudentClassEnrollment.class_instance_id,
        )
        .outerjoin(
            AcademicYear,
            AcademicYear.id == ClassInstance.academic_year_id,
        )
        .outerjoin(Class, Class.id == ClassInstance.class_id)
        .outerjoin(
            checkin,
            checkin.c.id == StudentAttendance.checkin_id,
        )
        .outerjoin(
            checkout,
            checkout.c.id == StudentAttendance.checkout_id,
        )
        .outerjoin(
            UserModel,
            UserModel.id == StudentAttendance.verified_by,
        )
        .where(
            StudentAttendance.date >= start,
            StudentAttendance.date <= end,
            and_(
                (AcademicYear.is_active.is_(True))
                | (AcademicYear.id.is_(None))
            ),
        )
        .order_by(StudentAttendance.date.desc(), Student.name.asc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )

    if class_instance_id:
        stmt = stmt.where(ClassInstance.id == class_instance_id)

    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (Student.name.ilike(like)) | (Student.nis.ilike(like))
        )

    if status_filter and status_filter.strip():
        stmt = stmt.where(StudentAttendance.status == status_filter.strip())

    rows = list(repo.db.execute(stmt).all())

    total_stmt = (
        select(StudentAttendance.id)
        .join(Student, Student.id == StudentAttendance.student_id)
        .outerjoin(
            StudentClassEnrollment,
            StudentClassEnrollment.student_id == Student.id,
        )
        .outerjoin(
            ClassInstance,
            ClassInstance.id == StudentClassEnrollment.class_instance_id,
        )
        .outerjoin(
            AcademicYear,
            AcademicYear.id == ClassInstance.academic_year_id,
        )
        .where(
            StudentAttendance.date >= start,
            StudentAttendance.date <= end,
            and_(
                (AcademicYear.is_active.is_(True))
                | (AcademicYear.id.is_(None))
            ),
        )
    )
    if class_instance_id:
        total_stmt = total_stmt.where(ClassInstance.id == class_instance_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        total_stmt = total_stmt.where(
            (Student.name.ilike(like)) | (Student.nis.ilike(like))
        )
    if status_filter and status_filter.strip():
        total_stmt = total_stmt.where(
            StudentAttendance.status == status_filter.strip()
        )

    total = len(list(repo.db.execute(total_stmt).all()))

    now_time = datetime.now().time().replace(microsecond=0)
    evidence_base = _evidence_dir()

    items: list[dict] = []
    for (
        sa_row,
        student_name,
        student_nis,
        class_name,
        in_time,
        out_time,
        verified_by_email,
    ) in rows:
        status_value = sa_row.status
        if sa_row.status not in {
            "IZIN_SAKIT",
            "IZIN_ACARA_KELUARGA",
            "IZIN_ACARA_KEAGAMAAN",
        }:
            if (
                in_time is None
                and out_time is None
                and sa_row.verified is False
            ):
                status_value = "TANPA_KETERANGAN"
            elif out_time is None and _should_mark_bolos(
                today=today,
                now_time=now_time,
                row_date=sa_row.date,
                gate_out_time=gate_out_time,
            ):
                status_value = "BOLOS"
            elif in_time is not None:
                status_value = (
                    "TELAT" if in_time > gate_in_time else "TEPAT_WAKTU"
                )

        has_evidence = any(
            evidence_base.glob(f"{sa_row.id}.*")
        )

        items.append(
            StudentAttendanceListItem(
                id=sa_row.id,
                student_id=sa_row.student_id,
                student_name=student_name,
                student_nis=student_nis,
                class_name=class_name,
                date=sa_row.date,
                checkin_time=in_time,
                checkout_time=out_time,
                status=status_value,
                verified=sa_row.verified,
                verified_at=sa_row.verified_at,
                verified_by_email=verified_by_email,
                has_evidence=has_evidence,
            ).model_dump()
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


@router.post("/leave", response_model=ApiResponse)
async def submit_leave(
    student_id: str = Form(...),
    date: str = Form(...),
    status_value: str = Form(..., alias="status"),
    evidence: UploadFile = File(...),
    repo: StudentAttendanceRepository = Depends(
        get_student_attendance_repository
    ),
    current_user: User = Depends(require_roles("ADMIN", "TEACHER")),
) -> ApiResponse:
    payload = StudentAttendanceLeaveCreate(
        student_id=uuid.UUID(student_id),
        date=dt_date.fromisoformat(date),
        status=status_value,
    )
    if payload.status not in {
        "IZIN_SAKIT",
        "IZIN_ACARA_KELUARGA",
        "IZIN_ACARA_KEAGAMAAN",
    }:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="invalid leave status",
            meta={},
        )

    row = repo.get_or_create(
        payload.student_id,
        payload.date,
        default_status=payload.status,
    )
    row.status = payload.status
    row.verified = True
    row.verified_at = datetime.now().astimezone()
    row.verified_by = current_user.id
    repo.db.add(row)
    repo.db.commit()
    repo.db.refresh(row)

    evidence_dir = _evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target = _evidence_path(row.id, evidence.filename or "evidence.jpg")
    content = await evidence.read()
    target.write_bytes(content)

    return build_response(
        status=status.HTTP_200_OK,
        data={"item": {"id": str(row.id)}},
        message="ok",
        meta={},
    )


@router.get("/{attendance_id}/evidence", response_model=None)
def get_evidence(
    attendance_id: uuid.UUID,
    repo: StudentAttendanceRepository = Depends(
        get_student_attendance_repository
    ),
    _: User = Depends(require_roles("ADMIN", "TEACHER")),
):
    row = repo.db.execute(
        select(StudentAttendance)
        .where(StudentAttendance.id == attendance_id)
        .limit(1)
    ).scalars().first()
    if row is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="not found",
            meta={},
        )

    evidence_base = _evidence_dir()
    matches = list(evidence_base.glob(f"{attendance_id}.*"))
    if not matches:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="evidence not found",
            meta={},
        )
    path = matches[0]
    return FileResponse(path)
