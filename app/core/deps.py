import uuid

from app.core.exceptions import AppException
from app.core.jwt import decode_access_token
from app.db.session import get_db
from app.models import User
from app.repositories.academic_years import AcademicYearRepository
from app.repositories.attendances import AttendanceRepository
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.class_subject_assignments import \
    ClassSubjectAssignmentRepository
from app.repositories.class_subject_schedules import \
    ClassSubjectScheduleRepository
from app.repositories.classes import ClassRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.gate_attendances import GateAttendanceRepository
from app.repositories.school_settings import SchoolSettingRepository
from app.repositories.student_attendances import StudentAttendanceRepository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.repositories.users import UserRepository
from fastapi import Depends, Header
from sqlalchemy.orm import Session


def get_academic_year_repository(
    db: Session = Depends(get_db),
) -> AcademicYearRepository:
    return AcademicYearRepository(db)


def get_class_repository(
    db: Session = Depends(get_db),
) -> ClassRepository:
    return ClassRepository(db)


def get_class_instance_repository(
    db: Session = Depends(get_db),
) -> ClassInstanceRepository:
    return ClassInstanceRepository(db)


def get_student_repository(
    db: Session = Depends(get_db),
) -> StudentRepository:
    return StudentRepository(db)


def get_user_repository(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_teacher_repository(
    db: Session = Depends(get_db),
) -> TeacherRepository:
    return TeacherRepository(db)


def get_subject_repository(
    db: Session = Depends(get_db),
) -> SubjectRepository:
    return SubjectRepository(db)


def get_class_subject_schedule_repository(
    db: Session = Depends(get_db),
) -> ClassSubjectScheduleRepository:
    return ClassSubjectScheduleRepository(db)


def get_class_subject_assignment_repository(
    db: Session = Depends(get_db),
) -> ClassSubjectAssignmentRepository:
    return ClassSubjectAssignmentRepository(db)


def get_student_face_repository(
    db: Session = Depends(get_db),
) -> StudentFaceRepository:
    return StudentFaceRepository(db)


def get_enrollment_repository(
    db: Session = Depends(get_db),
) -> EnrollmentRepository:
    return EnrollmentRepository(db)


def get_attendance_repository(
    db: Session = Depends(get_db),
) -> AttendanceRepository:
    return AttendanceRepository(db)


def get_gate_attendance_repository(
    db: Session = Depends(get_db),
) -> GateAttendanceRepository:
    return GateAttendanceRepository(db)


def get_school_setting_repository(
    db: Session = Depends(get_db),
) -> SchoolSettingRepository:
    return SchoolSettingRepository(db)


def get_student_attendance_repository(
    db: Session = Depends(get_db),
) -> StudentAttendanceRepository:
    return StudentAttendanceRepository(db)


def get_current_user(
    authorization: str | None = Header(default=None),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    if not authorization:
        raise AppException(
            status_code=401,
            message="missing authorization token",
            meta={},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppException(
            status_code=401,
            message="invalid authorization header",
            meta={},
        )

    payload = decode_access_token(token)
    subject = payload.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except ValueError:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )

    user = repo.get(user_id)
    if not user or not user.is_active:
        raise AppException(
            status_code=401,
            message="invalid token",
            meta={},
        )
    return user


def require_roles(*roles: str):
    normalized = {r.strip().upper() for r in roles if r and r.strip()}

    def _dep(current_user: User = Depends(get_current_user)) -> User:
        current_role = str(getattr(current_user, "role", "")).strip().upper()
        if current_role not in normalized:
            raise AppException(
                status_code=403,
                message="forbidden",
                meta={
                    "required_roles": sorted(normalized),
                    "role": current_role,
                },
            )
        return current_user

    return _dep
