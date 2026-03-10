import uuid

from app.core.config import settings
from app.main import create_app
from fastapi.testclient import TestClient


class _FakeSession:
    def commit(self) -> None:
        return None

    def flush(self) -> None:
        return None

    def refresh(self, obj) -> None:
        return None


class _FakeStudentRepo:
    def __init__(self, existing_ids: set[uuid.UUID]) -> None:
        self._existing_ids = existing_ids

    def get(self, student_id: uuid.UUID):
        if student_id in self._existing_ids:
            return object()
        return None


class _FakeStudentFaceRepo:
    def __init__(self) -> None:
        self.db = _FakeSession()
        self._faces: dict[uuid.UUID, list[uuid.UUID]] = {}

    def add(self, face) -> None:
        if getattr(face, "id", None) is None:
            face.id = uuid.uuid4()
        student_id = face.student_id
        self._faces.setdefault(student_id, []).append(face.id)

    def list_by_student_id(self, student_id: uuid.UUID):
        faces = []
        for face_id in self._faces.get(student_id, []):
            faces.append(
                type(
                    "_Face",
                    (),
                    {
                        "id": face_id,
                        "student_id": student_id,
                        "created_at": __import__("datetime").datetime.now(),
                    },
                )()
            )
        return faces

    def get(self, face_id: uuid.UUID):
        for student_id, ids in self._faces.items():
            if face_id in ids:
                return type(
                    "_Face",
                    (),
                    {"id": face_id, "student_id": student_id},
                )()
        return None

    def delete(self, face) -> None:
        ids = self._faces.get(face.student_id, [])
        self._faces[face.student_id] = [i for i in ids if i != face.id]


def test_enroll_and_list_faces(monkeypatch) -> None:
    from app.api.v1.routes import students as students_route
    from app.core.deps import get_current_user
    from app.services import student_faces as student_faces_service

    student_id = uuid.uuid4()
    fake_student_repo = _FakeStudentRepo({student_id})
    fake_face_repo = _FakeStudentFaceRepo()

    monkeypatch.setattr(
        student_faces_service,
        "extract_single_face_embedding",
        lambda _: [0.0] * 512,
    )

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[students_route.get_student_repository] = (
        lambda: fake_student_repo
    )
    app.dependency_overrides[students_route.get_student_face_repository] = (
        lambda: fake_face_repo
    )

    client = TestClient(app)
    files = [
        ("images", ("a.jpg", b"fake", "image/jpeg")),
        ("images", ("b.jpg", b"fake", "image/jpeg")),
        ("images", ("c.jpg", b"fake", "image/jpeg")),
    ]
    resp = client.post(
        f"{settings.api_v1_prefix}/students/{student_id}/faces/enroll",
        files=files,
    )
    assert resp.status_code == 201
    payload = resp.json()
    assert payload["status"] == 201
    assert payload["data"]["item"]["student_id"] == str(student_id)
    assert payload["data"]["item"]["stored_count"] == 3
    assert len(payload["data"]["item"]["results"]) == 3
    assert all(r["stored"] is True for r in payload["data"]["item"]["results"])
    assert all(
        r["face_id"] is not None for r in payload["data"]["item"]["results"]
    )

    list_resp = client.get(
        f"{settings.api_v1_prefix}/students/{student_id}/faces"
    )
    assert list_resp.status_code == 200
    list_payload = list_resp.json()
    assert list_payload["status"] == 200
    assert list_payload["data"]["items"]
