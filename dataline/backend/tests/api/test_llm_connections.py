import pytest
import pytest_asyncio
from fastapi.testclient import TestClient


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def llm_connection(client: TestClient) -> dict:
    """Creates a single LLM connection and returns its data."""
    data = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "sk-test-key-123",
        "is_default": True,
    }
    response = client.post("/api/llm-connections/", json=data)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def two_llm_connections(client: TestClient) -> list[dict]:
    """Creates two LLM connections and returns their data."""
    conn1 = client.post("/api/llm-connections/", json={
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "sk-key-1",
        "is_default": True,
    }).json()
    conn2 = client.post("/api/llm-connections/", json={
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20240620",
        "api_key": "sk-ant-key-2",
        "is_default": False,
    }).json()
    return [conn1, conn2]


# ─── List ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_llm_connections_empty(client: TestClient) -> None:
    response = client.get("/api/llm-connections/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_llm_connections_returns_all(client: TestClient, two_llm_connections: list[dict]) -> None:
    response = client.get("/api/llm-connections/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    providers = {c["provider"] for c in data}
    assert providers == {"openai", "anthropic"}


# ─── Create ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_llm_connection(client: TestClient) -> None:
    payload = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "sk-test-123",
        "is_default": True,
    }
    response = client.post("/api/llm-connections/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4o-mini"
    assert data["is_default"] is True
    assert "id" in data
    # api_key should NOT be returned in response
    assert "api_key" not in data


@pytest.mark.asyncio
async def test_create_llm_connection_without_api_key(client: TestClient) -> None:
    payload = {
        "provider": "ollama",
        "model": "llama3",
        "is_default": False,
    }
    response = client.post("/api/llm-connections/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "ollama"
    assert data["model"] == "llama3"


@pytest.mark.asyncio
async def test_create_llm_connection_with_base_url(client: TestClient) -> None:
    payload = {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "sk-test",
        "base_url": "https://my-proxy.example.com/v1",
        "is_default": False,
    }
    response = client.post("/api/llm-connections/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["base_url"] == "https://my-proxy.example.com/v1"


@pytest.mark.asyncio
async def test_create_sets_only_one_default(client: TestClient) -> None:
    """When a new connection is created as default, previous default should be unset."""
    # Create first as default
    r1 = client.post("/api/llm-connections/", json={
        "provider": "openai", "model": "gpt-4o-mini", "is_default": True
    })
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    # Create second as default
    r2 = client.post("/api/llm-connections/", json={
        "provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "is_default": True
    })
    assert r2.status_code == 201

    # List and check only one default
    all_conns = client.get("/api/llm-connections/").json()
    defaults = [c for c in all_conns if c["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["provider"] == "anthropic"


# ─── Update ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_llm_connection(client: TestClient, llm_connection: dict) -> None:
    conn_id = llm_connection["id"]
    update = {"model": "gpt-4o", "provider": "openai"}
    response = client.put(f"/api/llm-connections/{conn_id}", json=update)
    assert response.status_code == 200
    assert response.json()["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_update_llm_connection_not_found(client: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.put(f"/api/llm-connections/{fake_id}", json={"model": "gpt-4o", "provider": "openai"})
    assert response.status_code == 404


# ─── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_llm_connection(client: TestClient, llm_connection: dict) -> None:
    conn_id = llm_connection["id"]
    response = client.delete(f"/api/llm-connections/{conn_id}")
    assert response.status_code == 204

    # Verify it's gone
    all_conns = client.get("/api/llm-connections/").json()
    ids = [c["id"] for c in all_conns]
    assert conn_id not in ids


@pytest.mark.asyncio
async def test_delete_llm_connection_not_found(client: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/api/llm-connections/{fake_id}")
    assert response.status_code == 404


# ─── Set Default ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_default_llm_connection(client: TestClient, two_llm_connections: list[dict]) -> None:
    conn1, conn2 = two_llm_connections
    # conn1 is default, conn2 is not
    assert conn1["is_default"] is True
    assert conn2["is_default"] is False

    # Set conn2 as default
    response = client.post(f"/api/llm-connections/{conn2['id']}/default")
    assert response.status_code == 200
    assert response.json()["is_default"] is True

    # Verify conn1 is no longer default
    all_conns = client.get("/api/llm-connections/").json()
    conn1_updated = next(c for c in all_conns if c["id"] == conn1["id"])
    conn2_updated = next(c for c in all_conns if c["id"] == conn2["id"])
    assert conn1_updated["is_default"] is False
    assert conn2_updated["is_default"] is True


@pytest.mark.asyncio
async def test_set_default_not_found(client: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(f"/api/llm-connections/{fake_id}/default")
    assert response.status_code == 404
