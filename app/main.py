from app.api.v1.router import api_router as api_v1_routes
from app.core.config import settings
from app.core.exception_handlers import (app_exception_handler,
                                         http_exception_handler,
                                         unhandled_exception_handler,
                                         validation_exception_handler)
from app.core.exceptions import AppException
from app.schemas.api_response import ApiResponse, build_response
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def create_app() -> FastAPI:
    app = FastAPI(title="Face Attendance Backend")

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/", response_model=ApiResponse)
    def root() -> ApiResponse:
        return build_response(
            status=200,
            data={"service": "face-attendance-backend"},
            message="ok",
            meta={},
        )

    api_v1_router = APIRouter(prefix=settings.api_v1_prefix)
    api_v1_router.include_router(api_v1_routes)
    app.include_router(api_v1_router)

    return app


app = create_app()
