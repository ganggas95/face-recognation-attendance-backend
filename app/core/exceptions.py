from dataclasses import dataclass
from typing import Any


@dataclass
class AppException(Exception):
    status_code: int
    message: str
    meta: dict[str, Any] | None = None
