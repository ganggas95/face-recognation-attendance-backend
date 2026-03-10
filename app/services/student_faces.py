from __future__ import annotations

import uuid

from app.core.exceptions import AppException
from app.core.face import extract_single_face_embedding
from app.models import StudentFace
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository
from app.schemas.student_faces import (StudentFaceEnrollResult,
                                       StudentFaceEnrollSummary)


def enroll_student_faces(
    *,
    student_repo: StudentRepository,
    face_repo: StudentFaceRepository,
    student_id: uuid.UUID,
    images: list[tuple[str, bytes]],
) -> StudentFaceEnrollSummary:
    student = student_repo.get(student_id)
    if not student:
        raise AppException(
            status_code=404,
            message="student not found",
            meta={"student_id": str(student_id)},
        )

    results: list[StudentFaceEnrollResult] = []
    stored_count = 0
    for filename, image_bytes in images:
        try:
            embedding = extract_single_face_embedding(image_bytes)
            face = StudentFace(student_id=student_id, embedding=embedding)
            face_repo.add(face)
            face_repo.db.flush()
            stored_count += 1
            results.append(
                StudentFaceEnrollResult(
                    filename=filename,
                    stored=True,
                    face_id=face.id,
                    error=None,
                )
            )
        except AppException as exc:
            results.append(
                StudentFaceEnrollResult(
                    filename=filename,
                    stored=False,
                    face_id=None,
                    error=exc.message,
                )
            )

    if stored_count == 0:
        raise AppException(
            status_code=422,
            message="no valid face images",
            meta={"results": [r.model_dump() for r in results]},
        )

    face_repo.db.commit()
    return StudentFaceEnrollSummary(
        student_id=student_id,
        stored_count=stored_count,
        results=results,
    )


def list_student_faces(
    *,
    student_repo: StudentRepository,
    face_repo: StudentFaceRepository,
    student_id: uuid.UUID,
) -> list[StudentFace]:
    student = student_repo.get(student_id)
    if not student:
        raise AppException(
            status_code=404,
            message="student not found",
            meta={"student_id": str(student_id)},
        )
    return face_repo.list_by_student_id(student_id)


def delete_student_face(
    *,
    student_repo: StudentRepository,
    face_repo: StudentFaceRepository,
    student_id: uuid.UUID,
    face_id: uuid.UUID,
) -> None:
    student = student_repo.get(student_id)
    if not student:
        raise AppException(
            status_code=404,
            message="student not found",
            meta={"student_id": str(student_id)},
        )

    face = face_repo.get(face_id)
    if not face or face.student_id != student_id:
        raise AppException(
            status_code=404,
            message="student face not found",
            meta={"student_id": str(student_id), "face_id": str(face_id)},
        )

    face_repo.delete(face)
    face_repo.db.commit()
