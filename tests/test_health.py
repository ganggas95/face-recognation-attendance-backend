from app.core.config import settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get(f"{settings.api_v1_prefix}/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": 200,
        "data": {"status": "ok"},
        "message": "ok",
        "meta": {},
    }


def test_not_found_wrapped() -> None:
    client = TestClient(create_app())
    response = client.get("/__not_found__")
    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == 404
    assert payload["data"] == {}
    assert isinstance(payload["message"], str)
    assert isinstance(payload["meta"], dict)


def test_validation_error_wrapped() -> None:
    from app.core.deps import get_current_user

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    client = TestClient(app)
    response = client.post(f"{settings.api_v1_prefix}/attendance/verify")
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == 422
    assert payload["data"] == {}
    assert payload["message"] == "validation error"
    assert "errors" in payload["meta"]


def test_enrollment_create_and_duplicate() -> None:
    import uuid
    from datetime import datetime

    from app.api.v1.routes import enrollments as enrollments_route
    from app.core.deps import get_current_user

    class _FakeSession:
        def commit(self) -> None:
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

    class _FakeClassInstanceRepo:
        def __init__(self, existing_ids: set[uuid.UUID]) -> None:
            self._existing_ids = existing_ids

        def get(self, class_instance_id: uuid.UUID):
            if class_instance_id in self._existing_ids:
                return object()
            return None

    class _FakeEnrollmentRepo:
        def __init__(self) -> None:
            self.db = _FakeSession()
            self._existing: set[tuple[uuid.UUID, uuid.UUID]] = set()

        def add(self, enrollment) -> None:
            if getattr(enrollment, "id", None) is None:
                enrollment.id = uuid.uuid4()
            if getattr(enrollment, "created_at", None) is None:
                enrollment.created_at = datetime.now()
            self._existing.add(
                (enrollment.student_id, enrollment.class_instance_id)
            )

        def get_by_student_class_instance(
            self, *, student_id: uuid.UUID, class_instance_id: uuid.UUID
        ):
            if (student_id, class_instance_id) in self._existing:
                return object()
            return None

    student_id = uuid.uuid4()
    class_instance_id = uuid.uuid4()
    fake_student_repo = _FakeStudentRepo({student_id})
    fake_class_instance_repo = _FakeClassInstanceRepo({class_instance_id})
    fake_enrollment_repo = _FakeEnrollmentRepo()

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        enrollments_route.get_student_repository
    ] = lambda: fake_student_repo
    app.dependency_overrides[
        enrollments_route.get_class_instance_repository
    ] = lambda: fake_class_instance_repo
    app.dependency_overrides[
        enrollments_route.get_enrollment_repository
    ] = lambda: fake_enrollment_repo

    client = TestClient(app)
    payload = {
        "student_id": str(student_id),
        "class_instance_id": str(class_instance_id),
    }

    created = client.post(
        f"{settings.api_v1_prefix}/enrollments",
        json=payload,
    )
    assert created.status_code == 201

    duplicate = client.post(
        f"{settings.api_v1_prefix}/enrollments",
        json=payload,
    )
    assert duplicate.status_code == 409


def test_enrollment_list_by_student_ids() -> None:
    import uuid
    from datetime import datetime

    from app.api.v1.routes import enrollments as enrollments_route
    from app.core.deps import get_current_user

    class _Enrollment:
        def __init__(
            self,
            *,
            enrollment_id: uuid.UUID,
            student_id: uuid.UUID,
            class_instance_id: uuid.UUID,
        ) -> None:
            self.id = enrollment_id
            self.student_id = student_id
            self.class_instance_id = class_instance_id
            self.created_at = datetime.now()

    class _FakeEnrollmentRepo:
        def __init__(self, enrollments: list[_Enrollment]) -> None:
            self._enrollments = enrollments
            self.called_active_only: bool | None = None

        def list_by_student_ids(
            self,
            *,
            student_ids: list[uuid.UUID] | None = None,
            active_academic_year_only: bool = True,
        ):
            self.called_active_only = active_academic_year_only
            if not student_ids:
                return list(self._enrollments)
            return [
                e for e in self._enrollments if e.student_id in student_ids
            ]

    student_a = uuid.uuid4()
    student_b = uuid.uuid4()
    enrollment_a = _Enrollment(
        enrollment_id=uuid.uuid4(),
        student_id=student_a,
        class_instance_id=uuid.uuid4(),
    )
    enrollment_b = _Enrollment(
        enrollment_id=uuid.uuid4(),
        student_id=student_b,
        class_instance_id=uuid.uuid4(),
    )
    fake_repo = _FakeEnrollmentRepo([enrollment_a, enrollment_b])

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        enrollments_route.get_enrollment_repository
    ] = lambda: fake_repo

    client = TestClient(app)
    response = client.get(
        f"{settings.api_v1_prefix}/enrollments"
        f"?student_ids={student_a},{student_b}"
        "&active_academic_year_only=false"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == 200
    assert payload["message"] == "ok"
    assert payload["meta"]["count"] == 2
    assert fake_repo.called_active_only is False


def test_class_subject_assignment_create_and_duplicate() -> None:
    import uuid
    from datetime import datetime

    from app.api.v1.routes import \
        class_subject_assignments as assignments_route
    from app.core.deps import get_current_user

    class _FakeSession:
        def commit(self) -> None:
            return None

        def refresh(self, obj) -> None:
            return None

    class _FakeClassInstanceRepo:
        def __init__(self, existing_ids: set[uuid.UUID]) -> None:
            self._existing_ids = existing_ids

        def get(self, class_instance_id: uuid.UUID):
            if class_instance_id in self._existing_ids:
                return object()
            return None

    class _FakeSubjectRepo:
        def __init__(self, existing_ids: set[uuid.UUID]) -> None:
            self._existing_ids = existing_ids

        def get(self, subject_id: uuid.UUID):
            if subject_id in self._existing_ids:
                return object()
            return None

    class _FakeTeacherRepo:
        def __init__(self, existing_ids: set[uuid.UUID]) -> None:
            self._existing_ids = existing_ids

        def get(self, teacher_id: uuid.UUID):
            if teacher_id in self._existing_ids:
                return object()
            return None

    class _FakeAssignmentRepo:
        def __init__(self) -> None:
            self.db = _FakeSession()
            self._existing: set[tuple[uuid.UUID, uuid.UUID]] = set()

        def add(self, assignment) -> None:
            if getattr(assignment, "id", None) is None:
                assignment.id = uuid.uuid4()
            if getattr(assignment, "created_at", None) is None:
                assignment.created_at = datetime.now()
            self._existing.add(
                (assignment.class_instance_id, assignment.subject_id)
            )

        def get_by_class_instance_subject(
            self, *, class_instance_id: uuid.UUID, subject_id: uuid.UUID
        ):
            if (class_instance_id, subject_id) in self._existing:
                return object()
            return None

        def get(self, assignment_id: uuid.UUID):
            return None

    class_instance_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    teacher_id = uuid.uuid4()

    fake_class_instance_repo = _FakeClassInstanceRepo({class_instance_id})
    fake_subject_repo = _FakeSubjectRepo({subject_id})
    fake_teacher_repo = _FakeTeacherRepo({teacher_id})
    fake_assignment_repo = _FakeAssignmentRepo()

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        assignments_route.get_class_instance_repository
    ] = lambda: fake_class_instance_repo
    app.dependency_overrides[
        assignments_route.get_subject_repository
    ] = lambda: fake_subject_repo
    app.dependency_overrides[
        assignments_route.get_teacher_repository
    ] = lambda: fake_teacher_repo
    app.dependency_overrides[
        assignments_route.get_class_subject_assignment_repository
    ] = lambda: fake_assignment_repo

    client = TestClient(app)
    payload = {
        "class_instance_id": str(class_instance_id),
        "subject_id": str(subject_id),
        "teacher_id": str(teacher_id),
    }

    created = client.post(
        f"{settings.api_v1_prefix}/class-subject-assignments",
        json=payload,
    )
    assert created.status_code == 201

    duplicate = client.post(
        f"{settings.api_v1_prefix}/class-subject-assignments",
        json=payload,
    )
    assert duplicate.status_code == 409


def test_schedule_create_using_assignment() -> None:
    import uuid
    from datetime import datetime

    from app.api.v1.routes import class_subject_schedules as schedules_route
    from app.core.deps import get_current_user

    class _FakeSession:
        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

        def refresh(self, obj) -> None:
            return None

    class _FakeScheduleRepo:
        def __init__(self) -> None:
            self.db = _FakeSession()

        def add(self, schedule) -> None:
            if getattr(schedule, "id", None) is None:
                schedule.id = uuid.uuid4()
            if getattr(schedule, "created_at", None) is None:
                schedule.created_at = datetime.now()

    class _FakeAssignmentRepo:
        def __init__(
            self,
            *,
            assignment_id: uuid.UUID,
            class_instance_id: uuid.UUID,
            subject_id: uuid.UUID,
            teacher_id: uuid.UUID,
        ) -> None:
            self._assignment_id = assignment_id
            self._class_instance_id = class_instance_id
            self._subject_id = subject_id
            self._teacher_id = teacher_id

        def get(self, assignment_id: uuid.UUID):
            if assignment_id != self._assignment_id:
                return None
            return type(
                "_Assignment",
                (),
                {
                    "id": self._assignment_id,
                    "class_instance_id": self._class_instance_id,
                    "subject_id": self._subject_id,
                    "teacher_id": self._teacher_id,
                },
            )()

    class _UnusedRepo:
        def get(self, _id):
            return object()

    assignment_id = uuid.uuid4()
    class_instance_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    teacher_id = uuid.uuid4()

    fake_schedule_repo = _FakeScheduleRepo()
    fake_assignment_repo = _FakeAssignmentRepo(
        assignment_id=assignment_id,
        class_instance_id=class_instance_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
    )

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        schedules_route.get_class_subject_schedule_repository
    ] = lambda: fake_schedule_repo
    app.dependency_overrides[
        schedules_route.get_class_instance_repository
    ] = lambda: _UnusedRepo()
    app.dependency_overrides[
        schedules_route.get_subject_repository
    ] = lambda: _UnusedRepo()
    app.dependency_overrides[
        schedules_route.get_teacher_repository
    ] = lambda: _UnusedRepo()
    app.dependency_overrides[
        schedules_route.get_class_subject_assignment_repository
    ] = lambda: fake_assignment_repo

    client = TestClient(app)
    payload = {
        "class_subject_assignment_id": str(assignment_id),
        "day_of_week": 1,
        "start_time": "07:30:00",
        "end_time": "08:30:00",
        "room": "R-1",
    }
    resp = client.post(
        f"{settings.api_v1_prefix}/class-subject-schedules",
        json=payload,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["item"]["class_instance_id"] == str(class_instance_id)
    assert body["data"]["item"]["subject_id"] == str(subject_id)
    assert body["data"]["item"]["teacher_id"] == str(teacher_id)
    assert body["data"]["item"]["class_subject_assignment_id"] == str(
        assignment_id
    )


def test_class_instance_options() -> None:
    import uuid

    from app.api.v1.routes import class_instances as class_instances_route
    from app.core.deps import get_current_user

    class _FakeClass:
        def __init__(self, *, grade: int, name: str) -> None:
            self.grade = grade
            self.name = name

    class _FakeAcademicYear:
        def __init__(self, *, name: str, is_active: bool) -> None:
            self.name = name
            self.is_active = is_active

    class _FakeClassInstance:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.class_id = uuid.uuid4()
            self.academic_year_id = uuid.uuid4()
            self.class_template = _FakeClass(grade=1, name="A")
            self.academic_year = _FakeAcademicYear(
                name="2026/2027",
                is_active=True,
            )

    class _FakeClassInstanceRepo:
        def list_options(
            self,
            *,
            active_academic_year_only: bool = True,
            teacher_id=None,
        ):
            _ = teacher_id
            return [_FakeClassInstance()]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        class_instances_route.get_class_instance_repository
    ] = lambda: _FakeClassInstanceRepo()
    app.dependency_overrides[class_instances_route.get_teacher_repository] = (
        lambda: object()
    )

    client = TestClient(app)
    response = client.get(f"{settings.api_v1_prefix}/class-instances/options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == 200
    assert payload["message"] == "ok"
    assert "items" in payload["data"]
    assert payload["meta"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["id"]
    assert item["class_id"]
    assert item["academic_year_id"]
    assert "Kelas" in item["label"]


def test_teacher_options() -> None:
    import uuid

    from app.api.v1.routes import teachers as teachers_route
    from app.core.deps import get_current_user

    class _FakeTeacher:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.user_id = uuid.uuid4()
            self.name = "Guru A"
            self.nip = None
            self.phone = None

    class _FakeRepo:
        def list_options(self):
            return [_FakeTeacher()]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[teachers_route.get_teacher_repository] = (
        lambda: _FakeRepo()
    )

    client = TestClient(app)
    response = client.get(f"{settings.api_v1_prefix}/teachers/options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == 200
    assert payload["message"] == "ok"
    assert payload["meta"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["id"]
    assert item["user_id"]
    assert item["name"] == "Guru A"
    assert item["label"] == "Guru A"


def test_subject_options() -> None:
    import uuid

    from app.api.v1.routes import subjects as subjects_route
    from app.core.deps import get_current_user

    class _FakeSubject:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.code = "MAT"
            self.name = "Matematika"
            self.teacher_id = uuid.uuid4()

    class _FakeRepo:
        def list_options(self):
            return [_FakeSubject()]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[subjects_route.get_subject_repository] = (
        lambda: _FakeRepo()
    )
    app.dependency_overrides[subjects_route.get_teacher_repository] = (
        lambda: object()
    )

    client = TestClient(app)
    response = client.get(f"{settings.api_v1_prefix}/subjects/options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["id"]
    assert item["teacher_id"]
    assert item["code"] == "MAT"
    assert item["name"] == "Matematika"
    assert "MAT" in item["label"]
    assert "Matematika" in item["label"]


def test_class_subject_assignment_options() -> None:
    import uuid

    from app.api.v1.routes import \
        class_subject_assignments as assignments_route
    from app.core.deps import get_current_user

    class _FakeClass:
        def __init__(self, *, grade: int, name: str) -> None:
            self.grade = grade
            self.name = name

    class _FakeAcademicYear:
        def __init__(self, *, name: str, is_active: bool) -> None:
            self.name = name
            self.is_active = is_active

    class _FakeClassInstance:
        def __init__(self) -> None:
            self.class_template = _FakeClass(grade=2, name="B")
            self.academic_year = _FakeAcademicYear(
                name="2026/2027",
                is_active=True,
            )

    class _FakeSubject:
        def __init__(self, *, name: str) -> None:
            self.name = name

    class _FakeTeacher:
        def __init__(self, *, name: str) -> None:
            self.name = name

    class _FakeAssignment:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.class_instance_id = uuid.uuid4()
            self.subject_id = uuid.uuid4()
            self.teacher_id = uuid.uuid4()
            self.class_instance = _FakeClassInstance()
            self.subject = _FakeSubject(name="Matematika")
            self.teacher = _FakeTeacher(name="Guru A")

    class _FakeRepo:
        def list_options(self, *, active_academic_year_only: bool = True):
            return [_FakeAssignment()]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        assignments_route.get_class_subject_assignment_repository
    ] = lambda: _FakeRepo()

    client = TestClient(app)
    response = client.get(
        f"{settings.api_v1_prefix}/class-subject-assignments/options"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["id"]
    assert item["class_instance_id"]
    assert item["subject_id"]
    assert item["teacher_id"]
    assert "Matematika" in item["label"]


def test_class_subject_schedule_options() -> None:
    import uuid
    from datetime import time as dt_time

    from app.api.v1.routes import class_subject_schedules as schedules_route
    from app.core.deps import get_current_user

    class _FakeClass:
        def __init__(self, *, grade: int, name: str) -> None:
            self.grade = grade
            self.name = name

    class _FakeAcademicYear:
        def __init__(self, *, name: str, is_active: bool) -> None:
            self.name = name
            self.is_active = is_active

    class _FakeClassInstance:
        def __init__(self) -> None:
            self.class_template = _FakeClass(grade=3, name="C")
            self.academic_year = _FakeAcademicYear(
                name="2026/2027",
                is_active=True,
            )

    class _FakeSubject:
        def __init__(self, *, name: str) -> None:
            self.name = name

    class _FakeTeacher:
        def __init__(self, *, name: str) -> None:
            self.name = name

    class _FakeSchedule:
        def __init__(self) -> None:
            self.id = uuid.uuid4()
            self.class_instance_id = uuid.uuid4()
            self.subject_id = uuid.uuid4()
            self.teacher_id = uuid.uuid4()
            self.class_subject_assignment_id = None
            self.day_of_week = 1
            self.start_time = dt_time(hour=7, minute=30)
            self.end_time = dt_time(hour=8, minute=30)
            self.room = "R-1"
            self.class_instance = _FakeClassInstance()
            self.subject = _FakeSubject(name="Bahasa")
            self.teacher = _FakeTeacher(name="Guru B")

    class _FakeRepo:
        def list_options(
            self,
            *,
            active_academic_year_only: bool = True,
            teacher_id=None,
        ):
            _ = teacher_id
            return [_FakeSchedule()]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: object()
    app.dependency_overrides[
        schedules_route.get_class_subject_schedule_repository
    ] = lambda: _FakeRepo()
    app.dependency_overrides[schedules_route.get_teacher_repository] = (
        lambda: object()
    )

    client = TestClient(app)
    response = client.get(
        f"{settings.api_v1_prefix}/class-subject-schedules/options"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["id"]
    assert item["day_of_week"] == 1
    assert item["start_time"] == "07:30:00"
    assert item["end_time"] == "08:30:00"
    assert item["room"] == "R-1"
    assert "Senin" in item["label"]
