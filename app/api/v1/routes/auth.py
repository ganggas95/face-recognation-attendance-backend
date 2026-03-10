from app.core.exceptions import AppException
from app.core.deps import get_current_user, get_user_repository
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.users import UserRead
from app.services.auth import login, refresh_tokens
from fastapi import APIRouter, Depends, Header, status

router = APIRouter()


@router.post("/login", response_model=ApiResponse)
def login_route(
    payload: LoginRequest,
    repo: UserRepository = Depends(get_user_repository),
) -> ApiResponse:
    access_token, refresh_token = login(
        repo,
        email=payload.email,
        password=payload.password,
    )
    data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    ).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"token": data},
        message="ok",
        meta={},
    )


@router.post("/refresh", response_model=ApiResponse)
def refresh_route(
    authorization: str | None = Header(default=None),
    repo: UserRepository = Depends(get_user_repository),
) -> ApiResponse:
    if not authorization:
        raise AppException(
            status_code=401,
            message="missing authorization token",
            meta={},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppException(
            status_code=401,
            message="invalid authorization header",
            meta={},
        )
    access_token, refresh_token = refresh_tokens(repo, refresh_token=token)
    data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    ).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"token": data},
        message="ok",
        meta={},
    )


@router.get("/me", response_model=ApiResponse)
def me(current_user: User = Depends(get_current_user)) -> ApiResponse:
    item = UserRead.model_validate(current_user).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )
