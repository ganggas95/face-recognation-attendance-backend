from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StudentCreate(BaseModel):
    nis: str
    name: str
    gender: str | None = None
    birth_date: date | None = None
    address: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None


class StudentUpdate(BaseModel):
    nis: str | None = None
    name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    address: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nis: str
    name: str
    gender: str | None
    birth_date: date | None
    address: str | None
    guardian_name: str | None
    guardian_phone: str | None
    created_at: datetime
