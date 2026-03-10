import uuid
from datetime import date as dt_date
from datetime import datetime
from datetime import time as dt_time

from pydantic import BaseModel, ConfigDict


class StudentAttendanceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_nis: str
    class_name: str | None
    date: dt_date
    checkin_time: dt_time | None
    checkout_time: dt_time | None
    status: str
    verified: bool
    verified_at: datetime | None
    verified_by_email: str | None
    has_evidence: bool


class StudentAttendanceLeaveCreate(BaseModel):
    student_id: uuid.UUID
    date: dt_date
    status: str

