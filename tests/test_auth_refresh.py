import uuid

from app.core.config import settings
from app.core.security import hash_password
from app.main import create_app
from fastapi.testclient import TestClient


class _FakeUser:
    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        email: str,
        password: str,
    ) -> None:
        self.id = user_id
        self.email = email
        self.password_hash = hash_password(password)
        self.is_active = True


class _FakeUserRepo:
    def __init__(self, user: _FakeUser) -> None:
        self._user = user

    def get_by_email(self, email: str):
        return self._user if email == self._user.email else None

    def get(self, user_id: uuid.UUID):
        return self._user if user_id == self._user.id else None


def test_auth_login_and_refresh() -> None:
    from app.api.v1.routes import auth as auth_route

    user_id = uuid.uuid4()
    user = _FakeUser(user_id=user_id, email="a@b.com", password="pw")
    fake_repo = _FakeUserRepo(user)

    app = create_app()
    app.dependency_overrides[auth_route.get_user_repository] = (
        lambda: fake_repo
    )
    client = TestClient(app)

    login_resp = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": "a@b.com", "password": "pw"},
    )
    assert login_resp.status_code == 200
    login_payload = login_resp.json()
    access_token = login_payload["data"]["token"]["access_token"]
    refresh_token = login_payload["data"]["token"]["refresh_token"]
    assert isinstance(access_token, str) and access_token
    assert isinstance(refresh_token, str) and refresh_token

    refresh_resp = client.post(
        f"{settings.api_v1_prefix}/auth/refresh",
        headers={"authorization": f"Bearer {refresh_token}"},
    )
    assert refresh_resp.status_code == 200
    refresh_payload = refresh_resp.json()
    new_access = refresh_payload["data"]["token"]["access_token"]
    new_refresh = refresh_payload["data"]["token"]["refresh_token"]
    assert isinstance(new_access, str) and new_access
    assert isinstance(new_refresh, str) and new_refresh


def test_auth_refresh_rejects_invalid_token() -> None:
    client = TestClient(create_app())
    resp = client.post(
        f"{settings.api_v1_prefix}/auth/refresh",
        headers={"authorization": "Bearer invalid"},
    )
    assert resp.status_code == 401
