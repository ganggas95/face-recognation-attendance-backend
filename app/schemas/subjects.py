from datetime import datetime
from uuid import UUID

from app.schemas.teachers import TeacherRead
from pydantic import BaseModel, ConfigDict


class SubjectCreate(BaseModel):
    code: str | None = None
    name: str
    teacher_id: UUID | None = None


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str | None
    name: str
    teacher_id: UUID | None
    teacher: TeacherRead | None
    created_at: datetime
