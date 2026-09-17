"""Tests for Issue #4: cache chat member IDs in WebSocket broadcast.

`get_chat_member_ids()` must serve member lookups from Redis (with a DB
fallback that repopulates the cache), and the cache must be invalidated when
membership changes so a broadcast never serves a stale member list.
"""
import os
import tempfile
import json
import asyncio
from uuid import uuid4

TEST_DB = os.path.join(tempfile.gettempdir(), f"chat_app_test_issue4_{uuid4().hex[:8]}.db")
for suffix in ("", "-wal", "-shm"):
    if os.path.exists(TEST_DB + suffix):
        os.remove(TEST_DB + suffix)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"

import pytest
from fastapi.testclient import TestClient

import main
from main import app, limiter, async_session
from main import get_chat_member_ids, invalidate_chat_members_cache
from sqlalchemy import select
from main import ChatMember

limiter.enabled = False


class FakeRedis:
    """Minimal in-memory stand-in for a redis client (get/setex/delete)."""

    def __init__(self):
        self._data = {}

    async def get(self, key):
        return self._data.get(key)

    async def setex(self, key, ttl, value):
        self._data[key] = value

    async def delete(self, *keys):
        for k in keys:
            self._data.pop(k, None)

    def __contains__(self, key):
        return key in self._data


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(TEST_DB + suffix):
            os.remove(TEST_DB + suffix)


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = FakeRedis()
    main.redis_client = fake
    yield fake
    main.redis_client = None


def run(coro):
    return asyncio.run(coro)


def register_user(client, name):
    resp = client.post(
        "/auth/register",
        json={
            "username": name,
            "email": f"{name}@test.com",
            "password": "password123",
            "display_name": name.capitalize(),
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def login(client, name):
    resp = client.post("/auth/login", json={"username": name, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def new_user(client):
    name = f"user_{uuid4().hex[:8]}"
    user = register_user(client, name)
    return name, user["id"], login(client, name)


def create_dm(client, token, other_id):
    resp = client.post(
        "/chats",
        json={"member_ids": [other_id], "is_group": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def member_ids_from_db(chat_id):
    async with async_session() as session:
        result = await session.execute(
            select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        )
        return list(result.scalars().all())


def test_get_chat_member_ids_populates_cache(client, fake_redis):
    _, user_a_id, token_a = new_user(client)
    _, user_b_id, _ = new_user(client)
    chat_id = create_dm(client, token_a, user_b_id)

    ids = run(get_chat_member_ids(chat_id))
    assert set(ids) == {user_a_id, user_b_id}
    assert f"chat:members:{chat_id}" in fake_redis


def test_cached_members_served_without_db_hit(client, fake_redis, monkeypatch):
    fake_redis._data["chat:members:999"] = json.dumps([101, 202])

    def boom(*args, **kwargs):
        raise AssertionError("SQL DB should not be queried for cached member IDs")

    monkeypatch.setattr(main, "async_session", boom)
    ids = run(get_chat_member_ids(999))
    assert ids == [101, 202]


def test_invalidate_chat_members_cache(client, fake_redis):
    fake_redis._data["chat:members:555"] = json.dumps([1, 2, 3])
    run(invalidate_chat_members_cache(555))
    assert "chat:members:555" not in fake_redis


def test_refetch_after_invalidation(client, fake_redis):
    _, _, token_a = new_user(client)
    _, user_b_id, _ = new_user(client)
    chat_id = create_dm(client, token_a, user_b_id)

    run(get_chat_member_ids(chat_id))
    assert f"chat:members:{chat_id}" in fake_redis

    expected = run(member_ids_from_db(chat_id))

    run(invalidate_chat_members_cache(chat_id))
    assert f"chat:members:{chat_id}" not in fake_redis

    ids = run(get_chat_member_ids(chat_id))
    assert set(ids) == set(expected)
    assert f"chat:members:{chat_id}" in fake_redis


def test_leave_chat_invalidates_member_cache(client, fake_redis):
    _, _, token_a = new_user(client)
    _, user_b_id, token_b = new_user(client)
    chat_id = create_dm(client, token_a, user_b_id)

    run(get_chat_member_ids(chat_id))
    assert f"chat:members:{chat_id}" in fake_redis

    resp = client.post(
        f"/chats/{chat_id}/leave",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200, resp.text
    assert f"chat:members:{chat_id}" not in fake_redis


def test_broadcast_reaches_other_member(client, fake_redis):
    """A message sent over WS reaches the other chat member (broadcast path)."""
    _, _, token_a = new_user(client)
    _, user_b_id, token_b = new_user(client)
    chat_id = create_dm(client, token_a, user_b_id)

    with client.websocket_connect(f"/ws/{token_a}") as ws_a, client.websocket_connect(f"/ws/{token_b}") as ws_b:
        ws_a.send_json({"type": "message", "chat_id": chat_id, "content": "hello"})
        msg = ws_b.receive_json()
        assert msg["type"] == "message"
        assert msg["chat_id"] == chat_id
        assert msg["content"] == "hello"