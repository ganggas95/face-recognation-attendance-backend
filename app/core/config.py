from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


@dataclass(frozen=True)
class Settings:
    api_v1_prefix: str
    database_url: str | None
    jwt_secret_key: str | None
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int

    @staticmethod
    def from_env() -> "Settings":
        api_v1_prefix = (
            os.getenv("API_V1_PREFIX", "/api/v1").strip() or "/api/v1"
        )
        database_url = os.getenv("DATABASE_URL")
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        refresh_token_expire_minutes = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "43200")
        )
        return Settings(
            api_v1_prefix=api_v1_prefix,
            database_url=database_url,
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=jwt_algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_minutes=refresh_token_expire_minutes,
        )


settings = Settings.from_env()
