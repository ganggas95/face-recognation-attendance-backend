from datetime import time as dt_time

from app.core.deps import get_school_setting_repository, require_roles
from app.models import User
from app.repositories.school_settings import SchoolSettingRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.school_settings import SchoolSettingRead, SchoolSettingUpdate
from fastapi import APIRouter, Depends, status

router = APIRouter()


def _default_gate_in_time() -> dt_time:
    return dt_time(hour=7, minute=0, second=0)


def _default_gate_out_time() -> dt_time:
    return dt_time(hour=15, minute=0, second=0)


@router.get("", response_model=ApiResponse)
def get_default(
    repo: SchoolSettingRepository = Depends(get_school_setting_repository),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    item = repo.get_default()
    if item is None:
        item = repo.upsert_default(
            gate_in_time=_default_gate_in_time(),
            gate_out_time=_default_gate_out_time(),
        )
        repo.db.commit()
        repo.db.refresh(item)
    payload = SchoolSettingRead.model_validate(item).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": payload},
        message="ok",
        meta={},
    )


@router.put("", response_model=ApiResponse)
def update_default(
    payload: SchoolSettingUpdate,
    repo: SchoolSettingRepository = Depends(get_school_setting_repository),
    _: User = Depends(require_roles("ADMIN")),
) -> ApiResponse:
    item = repo.upsert_default(
        gate_in_time=payload.gate_in_time,
        gate_out_time=payload.gate_out_time,
    )
    repo.db.commit()
    repo.db.refresh(item)
    item_payload = SchoolSettingRead.model_validate(item).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item_payload},
        message="ok",
        meta={},
    )

