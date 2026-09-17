import asyncio
import base64
import json
import pytest

import main
from conftest import _register


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = b""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
        return None

    def json(self):
        return self._json


class FakeClient:
    posts = []
    responses = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, **kwargs):
        FakeClient.posts.append((url, kwargs))
        if FakeClient.responses:
            return FakeClient.responses.pop(0)
        return FakeResponse()


@pytest.fixture
def fake_httpx(monkeypatch):
    FakeClient.posts = []
    FakeClient.responses = [
        FakeResponse(json_data={"access_token": "fake-access-token", "expires_in": 3600})
    ]
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeClient)
    return FakeClient


def _load_service_account(monkeypatch):
    sa = {
        "type": "service_account",
        "project_id": "test-proj",
        "private_key_id": "kid123",
        "private_key": _rsa_pem(),
        "client_email": "test@test-proj.iam.gserviceaccount.com",
    }
    monkeypatch.setenv("FCM_PROJECT_ID", "test-proj")
    monkeypatch.setenv("FCM_SERVICE_ACCOUNT_JSON", json.dumps(sa))
    return sa


def _rsa_pem():
    rsa = __import__("cryptography").hazmat.primitives.asymmetric.rsa
    serialization = __import__("cryptography").hazmat.primitives.serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


async def _seed_device_tokens(user_id, tokens):
    async with main.async_session() as session:
        for token, platform in tokens:
            session.add(main.DeviceToken(user_id=user_id, token=token, platform=platform))
        await session.commit()


async def _get_user_id(username):
    async with main.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(main.User).where(main.User.username == username))
        return result.scalar_one().id


def test_truncate_push_content():
    assert main._truncate_push_content("short") == "short"
    long_content = "x" * 200
    truncated = main._truncate_push_content(long_content)
    assert len(truncated) == main.MAX_PUSH_CONTENT_LENGTH
    assert truncated.endswith("...")


@pytest.mark.asyncio
async def test_trigger_push_fcm(client, fake_httpx, monkeypatch):
    headers = _register(client, "alice")
    client.post("/users/device-token", json={"token": "fcm-token-1", "platform": "fcm"}, headers=headers)
    user_id = await _get_user_id("alice")
    _load_service_account(monkeypatch)

    await main.trigger_push_notifications(
        [user_id],
        {"type": "message", "chat_id": 5, "id": 99, "sender_id": 999, "content": "hello", "sender_name": "bob"},
        "bob",
    )

    urls = [url for url, _ in fake_httpx.posts]
    assert any(main.FCM_TOKEN_URL in url for url in urls)
    send_urls = [url for url in urls if "messages:send" in url]
    assert len(send_urls) == 1

    _, kwargs = [p for p in fake_httpx.posts if "messages:send" in p[0]][0]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    body = kwargs["json"]["message"]
    assert body["token"] == "fcm-token-1"
    assert body["notification"]["title"] == "bob"
    assert body["notification"]["body"] == "hello"


@pytest.mark.asyncio
async def test_trigger_push_apns(client, fake_httpx, monkeypatch):
    headers = _register(client, "dave")
    client.post("/users/device-token", json={"token": "apns-token-1", "platform": "apns"}, headers=headers)
    user_id = await _get_user_id("dave")

    monkeypatch.setenv("APNS_TEAM_ID", "TEAM123")
    monkeypatch.setenv("APNS_KEY_ID", "KEYID123")
    monkeypatch.setenv("APNS_BUNDLE_ID", "com.test.app")
    key_file = "/tmp/test-apns_key.p8"
    with open(key_file, "w") as f:
        f.write(_ec_p8_pem())
    monkeypatch.setenv("APNS_AUTH_KEY_FILE", key_file)

    await main.trigger_push_notifications(
        [user_id],
        {"type": "message", "chat_id": 7, "id": 12, "sender_id": 42, "content": "yo", "sender_name": "eve"},
        "eve",
    )

    send_urls = [url for url, _ in fake_httpx.posts if "/3/device/" in url]
    assert len(send_urls) == 1

    url, kwargs = [p for p in fake_httpx.posts if "/3/device/" in p[0]][0]
    assert url.endswith("/3/device/apns-token-1")
    assert kwargs["headers"]["apns-topic"] == "com.test.app"
    assert kwargs["headers"]["Authorization"].startswith("bearer ")
    assert kwargs["json"]["aps"]["alert"]["body"] == "yo"


def _ec_p8_pem():
    ec = __import__("cryptography").hazmat.primitives.asymmetric.ec
    serialization = __import__("cryptography").hazmat.primitives.serialization
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


@pytest.mark.asyncio
async def test_trigger_push_no_credentials_is_noop(client, fake_httpx, monkeypatch):
    headers = _register(client, "alice")
    client.post("/users/device-token", json={"token": "fcm-token-noop", "platform": "fcm"}, headers=headers)
    user_id = await _get_user_id("alice")

    monkeypatch.delenv("FCM_PROJECT_ID", raising=False)
    monkeypatch.delenv("FCM_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("APNS_TEAM_ID", raising=False)
    monkeypatch.delenv("APNS_AUTH_KEY_FILE", raising=False)

    await main.trigger_push_notifications(
        [user_id],
        {"type": "message", "chat_id": 5, "id": 99, "sender_id": 999, "content": "hello", "sender_name": "bob"},
        "bob",
    )

    assert fake_httpx.posts == []


@pytest.mark.asyncio
async def test_trigger_push_offline_users_only(client, fake_httpx, monkeypatch):
    alice_headers = _register(client, "alice")
    bob_headers = _register(client, "bob")
    client.post("/users/device-token", json={"token": "alice-tok", "platform": "fcm"}, headers=alice_headers)
    client.post("/users/device-token", json={"token": "bob-tok", "platform": "fcm"}, headers=bob_headers)
    _load_service_account(monkeypatch)

    alice_id = await _get_user_id("alice")

    # Only alice is offline (mirrors what the WebSocket handler passes in)
    await main.trigger_push_notifications(
        [alice_id],
        {"type": "message", "chat_id": 5, "id": 99, "sender_id": 999, "content": "hi", "sender_name": "eve"},
        "eve",
    )

    send_urls = [p for p in fake_httpx.posts if "messages:send" in p[0]]
    tokens = [p[1]["json"]["message"]["token"] for p in send_urls]
    assert tokens == ["alice-tok"]