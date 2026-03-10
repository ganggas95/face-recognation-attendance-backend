from app.schemas.api_response import ApiResponse, build_response
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=ApiResponse)
def health() -> ApiResponse:
    return build_response(
        status=200,
        data={"status": "ok"},
        message="ok",
        meta={},
    )
