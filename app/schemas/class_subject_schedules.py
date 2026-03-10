from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClassSubjectScheduleCreate(BaseModel):
    class_instance_id: UUID | None = None
    subject_id: UUID | None = None
    teacher_id: UUID | None = None
    class_subject_assignment_id: UUID | None = None
    day_of_week: int
    start_time: time
    end_time: time
    room: str | None = None


class ClassSubjectScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_instance_id: UUID
    subject_id: UUID
    teacher_id: UUID
    class_subject_assignment_id: UUID | None
    day_of_week: int
    start_time: time
    end_time: time
    room: str | None
    created_at: datetime
