from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AcademicYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = False


class AcademicYearRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
