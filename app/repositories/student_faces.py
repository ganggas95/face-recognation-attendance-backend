from __future__ import annotations

import uuid

from app.models import StudentFace
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class StudentFaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, face: StudentFace) -> None:
        self.db.add(face)

    def get(self, face_id: uuid.UUID) -> StudentFace | None:
        return self.db.get(StudentFace, face_id)

    def list_by_student_id(self, student_id: uuid.UUID) -> list[StudentFace]:
        stmt = (
            select(StudentFace)
            .where(StudentFace.student_id == student_id)
            .order_by(StudentFace.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def delete(self, face: StudentFace) -> None:
        self.db.delete(face)

    def best_matches_for_students(
        self,
        *,
        embedding: list[float],
        student_ids: list[uuid.UUID],
        limit: int = 2,
    ) -> list[tuple[uuid.UUID, float]]:
        if not student_ids:
            return []
        distance = StudentFace.embedding.cosine_distance(embedding).label(
            "distance"
        )
        stmt = (
            select(StudentFace.student_id, distance)
            .where(StudentFace.student_id.in_(student_ids))
            .order_by(distance.asc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [(row[0], float(row[1])) for row in rows]

    def count_for_student(self, student_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(StudentFace).where(
            StudentFace.student_id == student_id
        )
        return int(self.db.scalar(stmt) or 0)
