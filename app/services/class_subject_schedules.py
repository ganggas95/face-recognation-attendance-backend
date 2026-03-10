import uuid

from app.core.exceptions import AppException
from app.models import ClassSubjectSchedule
from app.repositories.class_instances import ClassInstanceRepository
from app.repositories.class_subject_assignments import (
    ClassSubjectAssignmentRepository,
)
from app.repositories.class_subject_schedules import (
    ClassSubjectScheduleRepository,
)
from app.repositories.subjects import SubjectRepository
from app.repositories.teachers import TeacherRepository
from app.schemas.class_subject_schedules import ClassSubjectScheduleCreate


def create_class_subject_schedule(
    schedule_repo: ClassSubjectScheduleRepository,
    class_instance_repo: ClassInstanceRepository,
    subject_repo: SubjectRepository,
    teacher_repo: TeacherRepository,
    assignment_repo: ClassSubjectAssignmentRepository,
    payload: ClassSubjectScheduleCreate,
) -> ClassSubjectSchedule:
    if payload.day_of_week < 0 or payload.day_of_week > 6:
        raise AppException(
            status_code=422,
            message="day_of_week must be between 0 and 6",
            meta={"day_of_week": payload.day_of_week},
        )

    if payload.class_subject_assignment_id is not None:
        assignment = assignment_repo.get(payload.class_subject_assignment_id)
        if not assignment:
            raise AppException(
                status_code=404,
                message="assignment not found",
                meta={
                    "class_subject_assignment_id": str(
                        payload.class_subject_assignment_id
                    )
                },
            )

        class_instance_id = assignment.class_instance_id
        subject_id = assignment.subject_id
        teacher_id = assignment.teacher_id
        class_subject_assignment_id = assignment.id
    else:
        if payload.class_instance_id is None:
            raise AppException(
                status_code=422,
                message="class_instance_id is required",
                meta={},
            )
        if payload.subject_id is None:
            raise AppException(
                status_code=422,
                message="subject_id is required",
                meta={},
            )
        if payload.teacher_id is None:
            raise AppException(
                status_code=422,
                message="teacher_id is required",
                meta={},
            )

        class_instance_id = payload.class_instance_id
        subject_id = payload.subject_id
        teacher_id = payload.teacher_id
        class_subject_assignment_id = None

        class_instance = class_instance_repo.get(class_instance_id)
        if not class_instance:
            raise AppException(
                status_code=404,
                message="class instance not found",
                meta={"class_instance_id": str(class_instance_id)},
            )

        teacher = teacher_repo.get(teacher_id)
        if not teacher:
            raise AppException(
                status_code=404,
                message="teacher not found",
                meta={"teacher_id": str(teacher_id)},
            )
        subject = subject_repo.get(subject_id)
        if not subject:
            raise AppException(
                status_code=404,
                message="subject not found",
                meta={"subject_id": str(subject_id)},
            )
        if subject.teacher_id is not None and subject.teacher_id != teacher_id:
            raise AppException(
                status_code=409,
                message="teacher does not match subject",
                meta={
                    "subject_id": str(subject_id),
                    "subject_teacher_id": str(subject.teacher_id),
                    "teacher_id": str(teacher_id),
                },
            )
    schedule = ClassSubjectSchedule(
        class_instance_id=class_instance_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        class_subject_assignment_id=class_subject_assignment_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room=payload.room,
    )
    schedule_repo.add(schedule)
    try:
        schedule_repo.db.commit()
    except Exception as exc:
        schedule_repo.db.rollback()
        raise AppException(
            status_code=409,
            message="schedule conflict",
            meta={"error": str(exc)},
        ) from exc
    schedule_repo.db.refresh(schedule)
    return schedule


def list_class_subject_schedules(
    repo: ClassSubjectScheduleRepository,
    *,
    offset: int,
    limit: int,
    class_instance_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    day_of_week: int | None = None,
) -> tuple[list[ClassSubjectSchedule], int]:
    return repo.list_paginated(
        offset=offset,
        limit=limit,
        class_instance_id=class_instance_id,
        teacher_id=teacher_id,
        day_of_week=day_of_week,
    )
