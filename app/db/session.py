from collections.abc import Generator
from functools import lru_cache

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@lru_cache(maxsize=1)
def _get_engine():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL env var is required")
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal(bind=_get_engine())
    try:
        yield db
    finally:
        db.close()
