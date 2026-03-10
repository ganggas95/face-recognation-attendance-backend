from app.core.exceptions import AppException
from app.schemas.api_response import build_response
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    payload = build_response(
        status=exc.status_code,
        data={},
        message=str(exc.detail),
        meta={},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
    )


def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    payload = build_response(
        status=422,
        data={},
        message="validation error",
        meta={"errors": exc.errors()},
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    payload = build_response(
        status=exc.status_code,
        data={},
        message=exc.message,
        meta=exc.meta or {},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
    )


def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    payload = build_response(
        status=500,
        data={},
        message="internal server error",
        meta={},
    )
    return JSONResponse(status_code=500, content=payload.model_dump())
