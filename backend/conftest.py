import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tempfile.NamedTemporaryFile(suffix='.db', delete=False).name}"
os.environ["JWT_SECRET"] = "test-secret-key-not-for-production"
os.environ.pop("REDIS_URL", None)

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client():
    main.limiter.enabled = False
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(autouse=True)
async def _reset_state():
    main._fcm_token = None
    main._fcm_token_expires_at = 0.0
    yield
    async with main.engine.begin() as conn:
        for table in reversed(main.Base.metadata.sorted_tables):
            await conn.execute(table.delete())


def _register(client, username):
    resp = client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@test.com", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    login = client.post(
        "/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}