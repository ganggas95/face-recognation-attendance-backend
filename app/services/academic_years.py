import uuid

from app.models import AcademicYear
from app.repositories.academic_years import AcademicYearRepository
from app.schemas.academic_years import AcademicYearCreate


def create_academic_year(
    repo: AcademicYearRepository,
    payload: AcademicYearCreate,
) -> AcademicYear:
    academic_year = AcademicYear(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_active=payload.is_active,
    )
    if payload.is_active:
        repo.deactivate_all()
        academic_year.is_active = True
    repo.add(academic_year)
    repo.db.commit()
    repo.db.refresh(academic_year)
    return academic_year


def list_academic_years(
    repo: AcademicYearRepository,
    *,
    offset: int,
    limit: int,
) -> tuple[list[AcademicYear], int]:
    return repo.list_paginated(offset=offset, limit=limit)


def activate_academic_year(
    repo: AcademicYearRepository,
    academic_year_id: uuid.UUID,
) -> AcademicYear | None:
    academic_year = repo.get(academic_year_id)
    if not academic_year:
        return None
    repo.deactivate_all()
    academic_year.is_active = True
    repo.db.commit()
    repo.db.refresh(academic_year)
    return academic_year
