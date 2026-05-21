import logging
from base64 import b64encode
from io import BytesIO

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


# ─── User Info ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_user_info_name(client: TestClient) -> None:
    user_in = {"name": "John"}
    response = client.patch("/settings/info", json=user_in)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "John"
    assert data["sentry_enabled"] is True
    assert data["analytics_enabled"] is True
    assert data["hide_sql_preference"] is False
    # Old openai fields should NOT be present
    assert "openai_api_key" not in data
    assert "preferred_openai_model" not in data
    assert "openai_base_url" not in data


@pytest.mark.asyncio
async def test_update_user_info_empty_name(client: TestClient) -> None:
    user_in = {"name": ""}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_info_long_name(client: TestClient) -> None:
    user_in = {"name": "a" * 251}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_info_sentry_flag(client: TestClient) -> None:
    user_in = {"sentry_enabled": False}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 200
    assert response.json()["data"]["sentry_enabled"] is False


@pytest.mark.asyncio
async def test_update_user_info_analytics_flag(client: TestClient) -> None:
    user_in = {"analytics_enabled": False}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 200
    assert response.json()["data"]["analytics_enabled"] is False


@pytest.mark.asyncio
async def test_update_user_info_hide_sql_preference(client: TestClient) -> None:
    user_in = {"hide_sql_preference": True}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 200
    assert response.json()["data"]["hide_sql_preference"] is True


@pytest.mark.asyncio
async def test_update_user_info_extra_fields_ignored(client: TestClient) -> None:
    user_in = {"name": "John", "extra": "extra"}
    response = client.patch("/settings/info", json=user_in)
    assert response.status_code == 200
    assert "extra" not in response.json()["data"]


@pytest.mark.asyncio
async def test_get_info_not_found(client: TestClient) -> None:
    response = client.get("/settings/info")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_info_after_create(client: TestClient) -> None:
    # Create user first
    client.patch("/settings/info", json={"name": "Alice"})
    # Then get
    response = client.get("/settings/info")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Alice"


# ─── Avatar ───────────────────────────────────────────────────────────────────

FileTuple = tuple[str, tuple[str, BytesIO, str]]


@pytest.fixture
def avatar_file() -> tuple[FileTuple, bytes]:
    file_data = b"test"
    file_name = "test_file.txt"
    file = ("file", (file_name, BytesIO(file_data), "image/jpeg"))
    return file, file_data


@pytest.mark.asyncio
async def test_upload_avatar(client: TestClient, avatar_file: tuple[FileTuple, bytes]) -> None:
    file, file_data = avatar_file
    base64_encoded = b64encode(file_data).decode("utf-8")

    response = client.post("/settings/avatar", files=[file])
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "blob": base64_encoded,
        },
    }


@pytest_asyncio.fixture
async def avatar(client: TestClient, avatar_file: tuple[FileTuple, bytes]) -> str:
    """Uploads an avatar and returns the base64 encoded blob."""
    file, _ = avatar_file
    response = client.post("/settings/avatar", files=[file])
    return response.json()["data"]["blob"]


@pytest.mark.asyncio
async def test_get_avatar(client: TestClient, avatar: str) -> None:
    response = client.get("/settings/avatar")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "blob": avatar,
        },
    }


@pytest.mark.asyncio
async def test_get_avatar_no_avatar(client: TestClient) -> None:
    response = client.get("/settings/avatar")
    assert response.status_code == 404
