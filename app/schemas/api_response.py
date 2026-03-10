from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    status: int
    data: dict[str, Any]
    message: str
    meta: dict[str, Any]


def build_response(
    *,
    status: int,
    data: dict[str, Any] | None = None,
    message: str = "",
    meta: dict[str, Any] | None = None,
) -> ApiResponse:
    return ApiResponse(
        status=status,
        data=data or {},
        message=message,
        meta=meta or {},
    )
