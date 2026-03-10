from datetime import datetime
from uuid import UUID

from app.schemas.users import UserRead
from pydantic import BaseModel, ConfigDict


class TeacherUserCreate(BaseModel):
    email: str
    password: str
    is_active: bool = True


class TeacherCreate(BaseModel):
    user: TeacherUserCreate
    name: str
    nip: str | None = None
    phone: str | None = None


class TeacherUpdate(BaseModel):
    name: str | None = None
    nip: str | None = None
    phone: str | None = None


class TeacherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: UserRead | None
    name: str
    nip: str | None
    phone: str | None
    created_at: datetime
