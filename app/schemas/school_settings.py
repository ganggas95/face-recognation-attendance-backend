from datetime import datetime
from datetime import time as dt_time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SchoolSettingUpdate(BaseModel):
    gate_in_time: dt_time
    gate_out_time: dt_time


class SchoolSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    gate_in_time: dt_time
    gate_out_time: dt_time
    created_at: datetime
    updated_at: datetime

