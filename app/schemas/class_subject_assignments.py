from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClassSubjectAssignmentCreate(BaseModel):
    class_instance_id: UUID
    subject_id: UUID
    teacher_id: UUID


class ClassSubjectAssignmentUpdate(BaseModel):
    teacher_id: UUID


class ClassSubjectAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_instance_id: UUID
    subject_id: UUID
    teacher_id: UUID
    created_at: datetime
