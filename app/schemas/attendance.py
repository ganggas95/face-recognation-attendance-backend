from uuid import UUID

from pydantic import BaseModel


class AttendanceVerifyResponse(BaseModel):
    matched: bool
    student_id: UUID | None = None
    confidence: float | None = None
