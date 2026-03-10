from app.core.exceptions import AppException
from app.models import Student
from app.repositories.students import StudentRepository
from app.schemas.students import StudentCreate, StudentUpdate


def create_student(repo: StudentRepository, payload: StudentCreate) -> Student:
    existing = repo.get_by_nis(payload.nis)
    if existing:
        raise AppException(
            status_code=409,
            message="student already exists",
            meta={"nis": payload.nis},
        )
    student = Student(
        nis=payload.nis,
        name=payload.name,
        gender=payload.gender,
        birth_date=payload.birth_date,
        address=payload.address,
        guardian_name=payload.guardian_name,
        guardian_phone=payload.guardian_phone,
    )
    repo.add(student)
    repo.db.commit()
    repo.db.refresh(student)
    return student


def get_student(repo: StudentRepository, student_id) -> Student:
    student = repo.get(student_id)
    if not student:
        raise AppException(status_code=404, message="student not found")
    return student


def update_student(
    repo: StudentRepository,
    *,
    student_id,
    payload: StudentUpdate,
) -> Student:
    student = get_student(repo, student_id)

    if "nis" in payload.model_fields_set:
        nis = (payload.nis or "").strip()
        if not nis:
            raise AppException(status_code=400, message="nis is required")
        existing = repo.get_by_nis(nis)
        if existing and existing.id != student.id:
            raise AppException(
                status_code=409,
                message="student already exists",
                meta={"nis": nis},
            )
        student.nis = nis

    if "name" in payload.model_fields_set:
        name = (payload.name or "").strip()
        if not name:
            raise AppException(status_code=400, message="name is required")
        student.name = name

    if "gender" in payload.model_fields_set:
        student.gender = (payload.gender or "").strip() or None
    if "birth_date" in payload.model_fields_set:
        student.birth_date = payload.birth_date
    if "address" in payload.model_fields_set:
        student.address = (payload.address or "").strip() or None
    if "guardian_name" in payload.model_fields_set:
        student.guardian_name = (payload.guardian_name or "").strip() or None
    if "guardian_phone" in payload.model_fields_set:
        student.guardian_phone = (payload.guardian_phone or "").strip() or None

    repo.db.commit()
    repo.db.refresh(student)
    return student


def list_students(
    repo: StudentRepository,
    *,
    offset: int,
    limit: int,
) -> tuple[list[Student], int]:
    return repo.list_paginated(offset=offset, limit=limit)
