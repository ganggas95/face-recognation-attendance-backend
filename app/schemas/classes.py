from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClassCreate(BaseModel):
    name: str
    grade: int
    homeroom_teacher_id: UUID | None = None
    academic_year_id: UUID | None = None


class ClassUpdate(BaseModel):
    name: str | None = None
    grade: int | None = None
    homeroom_teacher_id: UUID | None = None
    academic_year_id: UUID | None = None


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    grade: int
    homeroom_teacher_id: UUID | None
