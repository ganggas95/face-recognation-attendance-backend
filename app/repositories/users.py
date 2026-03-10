from __future__ import annotations

import uuid

from app.models import User
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, user: User) -> None:
        self.db.add(user)

    def delete(self, user: User) -> None:
        self.db.delete(user)

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        q: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User)
        total_stmt = select(func.count()).select_from(User)

        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))
            total_stmt = total_stmt.where(User.is_active.is_(is_active))

        if role is not None:
            r = role.strip()
            if r:
                stmt = stmt.where(User.role == r)
                total_stmt = total_stmt.where(User.role == r)

        if q:
            qq = q.strip()
            if qq:
                like = f"%{qq}%"
                stmt = stmt.where(User.email.ilike(like))
                total_stmt = total_stmt.where(User.email.ilike(like))

        total = int(self.db.scalar(total_stmt) or 0)
        stmt = (
            stmt.order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt))
        return items, total
