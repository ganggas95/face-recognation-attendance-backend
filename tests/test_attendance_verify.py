import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.main import create_app
from fastapi.testclient import TestClient


class _FakeSession:
    def commit(self) -> None:
        return None

    def refresh(self, obj) -> None:
        return None


class _Schedule:
    def __init__(
        self,
        schedule_id: uuid.UUID,
        class_instance_id: uuid.UUID,
        *,
        day_of_week: int,
        start_time: time,
        end_time: time,
    ):
        self.id = schedule_id
        self.class_instance_id = class_instance_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time


class _FakeScheduleRepo:
    def __init__(self, schedule: _Schedule | None) -> None:
        self._schedule = schedule

    def get(self, schedule_id: uuid.UUID):
        if self._schedule and self._schedule.id == schedule_id:
            return self._schedule
        return None


class _FakeEnrollmentRepo:
    def __init__(self, student_ids: list[uuid.UUID]) -> None:
        self._student_ids = student_ids

    def list_student_ids_by_class_instance(
        self, *, class_instance_id: uuid.UUID
    ):
        return list(self._student_ids)


class _FakeFaceRepo:
    def __init__(self, matches: list[tuple[uuid.UUID, float]]) -> None:
        self._matches = matches

    def best_matches_for_students(
        self,
        *,
        embedding,
        student_ids,
        limit: int = 2,
    ):
        return list(self._matches)[:limit]


class _FakeAttendanceRepo:
    def __init__(self) -> None:
        self.db = _FakeSession()
        self._existing: dict[tuple[uuid.UUID, uuid.UUID, date], object] = {}

    def add(self, attendance) -> None:
        if getattr(attendance, "id", None) is None:
            attendance.id = uuid.uuid4()
        key = (attendance.student_id, attendance.schedule_id, attendance.date)
        self._existing[key] = attendance

    def get_by_student_schedule_date(self, *, student_id, schedule_id, date):
        return self._existing.get((student_id, schedule_id, date))


class _FakeStudentRepo:
    def __init__(self, mapping: dict[uuid.UUID, str]) -> None:
        self._mapping = mapping

    def get(self, student_id: uuid.UUID):
        name = self._mapping.get(student_id)
        if not name:
            return None
        return type("_Student", (), {"id": student_id, "name": name})()


class _FakeAttendanceRepoList(_FakeAttendanceRepo):
    def __init__(self, items: list[object], total: int) -> None:
        super().__init__()
        self._items = items
        self._total = total

    def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        class_instance_id=None,
        subject_id=None,
        teacher_id=None,
        date=None,
        student_name=None,
    ):
        _ = (
            offset,
            limit,
            class_instance_id,
            subject_id,
            teacher_id,
            date,
            student_name,
        )
        return list(self._items), int(self._total)


def test_attendance_verify_matched(monkeypatch) -> None:
    from app.api.v1.routes import attendance as attendance_route
    from app.core.deps import get_current_user
    from app.services import attendance as attendance_service

    schedule_id = uuid.uuid4()
    class_instance_id = uuid.uuid4()
    student_id = uuid.uuid4()

    fake_schedule_repo = _FakeScheduleRepo(
        _Schedule(
            schedule_id,
            class_instance_id,
            day_of_week=1,
            start_time=time(9, 0, 0),
            end_time=time(10, 0, 0),
        )
    )
    fake_enrollment_repo = _FakeEnrollmentRepo([student_id])
    fake_face_repo = _FakeFaceRepo([(student_id, 0.1)])
    fake_attendance_repo = _FakeAttendanceRepo()
    fake_student_repo = _FakeStudentRepo({student_id: "Budi"})

    monkeypatch.setattr(
        attendance_service,
        "extract_single_face_embedding",
        lambda _: [0.0] * 512,
    )
    monkeypatch.setattr(
        attendance_service,
        "_now_local",
        lambda: datetime(2024, 1, 1, 9, 30, 0, tzinfo=ZoneInfo("UTC")),
    )

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        attendance_route.get_class_subject_schedule_repository
    ] = lambda: fake_schedule_repo
    app.dependency_overrides[
        attendance_route.get_enrollment_repository
    ] = lambda: fake_enrollment_repo
    app.dependency_overrides[
        attendance_route.get_student_face_repository
    ] = lambda: fake_face_repo
    app.dependency_overrides[
        attendance_route.get_attendance_repository
    ] = lambda: fake_attendance_repo
    app.dependency_overrides[
        attendance_route.get_student_repository
    ] = lambda: fake_student_repo

    client = TestClient(app)
    files = {"image": ("img.jpg", b"fake", "image/jpeg")}
    data = {"schedule_id": str(schedule_id)}
    resp = client.post(
        f"{settings.api_v1_prefix}/attendance/verify",
        files=files,
        data=data,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == 200
    assert payload["data"]["item"]["matched"] is True
    assert payload["data"]["item"]["student_id"] == str(student_id)
    assert payload["data"]["item"]["student_name"] == "Budi"
    assert payload["data"]["item"]["attendance_id"] is not None


def test_attendance_verify_rejected_outside_schedule(monkeypatch) -> None:
    from app.api.v1.routes import attendance as attendance_route
    from app.core.deps import get_current_user
    from app.services import attendance as attendance_service

    schedule_id = uuid.uuid4()
    class_instance_id = uuid.uuid4()
    student_id = uuid.uuid4()

    fake_schedule_repo = _FakeScheduleRepo(
        _Schedule(
            schedule_id,
            class_instance_id,
            day_of_week=1,
            start_time=time(9, 0, 0),
            end_time=time(10, 0, 0),
        )
    )
    fake_enrollment_repo = _FakeEnrollmentRepo([student_id])
    fake_face_repo = _FakeFaceRepo([(student_id, 0.1)])
    fake_attendance_repo = _FakeAttendanceRepo()
    fake_student_repo = _FakeStudentRepo({student_id: "Budi"})

    monkeypatch.setattr(
        attendance_service,
        "extract_single_face_embedding",
        lambda _: [0.0] * 512,
    )
    monkeypatch.setenv("ATTENDANCE_ENFORCE_SCHEDULE", "1")
    monkeypatch.setattr(
        attendance_service,
        "_now_local",
        lambda: datetime(2024, 1, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC")),
    )

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        attendance_route.get_class_subject_schedule_repository
    ] = lambda: fake_schedule_repo
    app.dependency_overrides[
        attendance_route.get_enrollment_repository
    ] = lambda: fake_enrollment_repo
    app.dependency_overrides[
        attendance_route.get_student_face_repository
    ] = lambda: fake_face_repo
    app.dependency_overrides[
        attendance_route.get_attendance_repository
    ] = lambda: fake_attendance_repo
    app.dependency_overrides[
        attendance_route.get_student_repository
    ] = lambda: fake_student_repo

    client = TestClient(app)
    files = {"image": ("img.jpg", b"fake", "image/jpeg")}
    data = {"schedule_id": str(schedule_id)}
    resp = client.post(
        f"{settings.api_v1_prefix}/attendance/verify",
        files=files,
        data=data,
    )
    assert resp.status_code == 422
    payload = resp.json()
    assert payload["status"] == 422
    expected_message = "attendance is not allowed outside schedule time"
    assert payload["message"] == expected_message
    assert payload["meta"]["reason"] in {"day_mismatch", "time_outside_window"}


def test_attendance_list(monkeypatch) -> None:
    from app.api.v1.routes import attendance as attendance_route
    from app.core.deps import get_current_user

    schedule_id = uuid.uuid4()
    class_instance_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    attendance_id = uuid.uuid4()

    cls = type("_Class", (), {"grade": 1, "name": "A"})()
    ci = type(
        "_ClassInstance",
        (),
        {"id": class_instance_id, "class_template": cls},
    )()
    subject = type("_Subject", (), {"id": subject_id, "name": "Matematika"})()
    teacher = type("_Teacher", (), {"id": teacher_id, "name": "Bu Sari"})()
    schedule = type(
        "_ScheduleList",
        (),
        {
            "id": schedule_id,
            "class_instance_id": class_instance_id,
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "class_instance": ci,
            "subject": subject,
            "teacher": teacher,
        },
    )()
    student = type(
        "_StudentList",
        (),
        {"id": student_id, "nis": "S001", "name": "Budi"},
    )()
    attendance = type(
        "_AttendanceList",
        (),
        {
            "id": attendance_id,
            "date": date(2024, 1, 1),
            "time": time(9, 30, 0),
            "status": "PRESENT",
            "confidence": 0.9,
            "student_id": student_id,
            "schedule_id": schedule_id,
            "student": student,
            "schedule": schedule,
        },
    )()

    fake_attendance_repo = _FakeAttendanceRepoList([attendance], 1)

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        attendance_route.get_attendance_repository
    ] = lambda: fake_attendance_repo

    client = TestClient(app)
    resp = client.get(
        f"{settings.api_v1_prefix}/attendance?page=1&page_size=20"
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == 200
    assert len(payload["data"]["items"]) == 1
    item = payload["data"]["items"][0]
    assert item["student_name"] == "Budi"
    assert item["subject_name"] == "Matematika"
