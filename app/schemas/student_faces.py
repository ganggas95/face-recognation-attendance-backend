from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudentFaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    created_at: datetime


class StudentFaceEnrollResult(BaseModel):
    filename: str
    stored: bool
    face_id: uuid.UUID | None = None
    error: str | None = None


class StudentFaceEnrollSummary(BaseModel):
    student_id: uuid.UUID
    stored_count: int
    results: list[StudentFaceEnrollResult]
