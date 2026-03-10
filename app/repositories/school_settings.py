from __future__ import annotations

from app.models import SchoolSetting
from sqlalchemy import select
from sqlalchemy.orm import Session


class SchoolSettingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_default(self) -> SchoolSetting | None:
        stmt = select(SchoolSetting).where(SchoolSetting.key == "default")
        return self.db.scalar(stmt)

    def upsert_default(
        self,
        *,
        gate_in_time,
        gate_out_time,
    ) -> SchoolSetting:
        item = self.get_default()
        if item is None:
            item = SchoolSetting(
                key="default",
                gate_in_time=gate_in_time,
                gate_out_time=gate_out_time,
            )
            self.db.add(item)
            return item
        item.gate_in_time = gate_in_time
        item.gate_out_time = gate_out_time
        return item

