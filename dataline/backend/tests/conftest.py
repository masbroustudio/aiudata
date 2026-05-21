import base64
import logging.config
import pathlib
from typing import AsyncGenerator, Generator
from unittest import mock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic.command import upgrade
from alembic.config import Config
from dataline.app import App
from dataline.config import config
from dataline.models.base import DBModel
from dataline.repositories.base import AsyncSession, get_session
from dataline.utils.posthog import posthog

logging.basicConfig(level=logging.INFO)

# Disable Posthog in tests
posthog.disabled = True


def pytest_addoption(parser):
    parser.addoption("--run-expensive", action="store_true", default=False, help="run expensive tests")


# https://docs.pytest.org/en/stable/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if not config.getoption("--run-expensive"):
        # --run-expensive not passed in cli: skip expensive tests
        skip_expensive = pytest.mark.skip(reason="need --run-expensive option to run")
        for item in items:
            if "expensive" in item.keywords:
                item.add_marker(skip_expensive)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine("sqlite+aiosqlite:///test.sqlite3")

    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA foreign_keys=ON"))
        await connection.run_sync(DBModel.metadata.drop_all)
        await connection.run_sync(DBModel.metadata.create_all)

    yield engine
    await engine.dispose()

    # Delete database after tests
    pathlib.Path("test.sqlite3").unlink(missing_ok=True)


@pytest_asyncio.fixture(scope="function")
async def session(engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session, session.begin():
        # prevent test from committing anything, only flush
        # only useful in case we move to real DBs not in-mem
        monkeypatch.setattr(session, "commit", mock.AsyncMock(wraps=session.flush))
        yield session
        await session.rollback()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    alembic_config = Config((pathlib.Path(__file__).parent.parent / "alembic.ini").resolve())
    alembic_config.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///test.sqlite3")
    alembic_config.config_file_name = None  # to prevent alembic from overriding the logs
    upgrade(alembic_config, "8e6f32050015")


app = App()


def _make_auth_cookie() -> str | None:
    """Build Basic auth cookie value if auth is configured."""
    if config.has_auth:
        token = base64.b64encode(
            f"{config.auth_username}:{config.auth_password}".encode("ascii")
        ).decode("utf-8")
        return f"Basic {token}"
    return None


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    def override_get_session() -> Generator[AsyncSession, None, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    auth_cookie = _make_auth_cookie()
    cookies = {"Authorization": auth_cookie} if auth_cookie else {}

    with TestClient(app=app, raise_server_exceptions=True, cookies=cookies) as client:
        yield client


pytest_plugins = ["tests.api.connection.conftest", "tests.api.conversation.conftest"]
