import pytest

from conftest import _register


def test_register_device_token_requires_auth(client):
    resp = client.post("/users/device-token", json={"token": "tok1", "platform": "fcm"})
    assert resp.status_code in (401, 403)


def test_register_device_token(client):
    headers = _register(client, "alice")
    resp = client.post("/users/device-token", json={"token": "tok1", "platform": "fcm"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "registered"}

    list_resp = client.get("/users/device-tokens", headers=headers)
    assert list_resp.status_code == 200
    tokens = list_resp.json()
    assert len(tokens) == 1
    assert tokens[0]["token"] == "tok1"
    assert tokens[0]["platform"] == "fcm"


def test_register_device_token_updates_existing(client):
    headers = _register(client, "bob")
    resp = client.post("/users/device-token", json={"token": "tok2", "platform": "fcm"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "registered"}

    resp = client.post("/users/device-token", json={"token": "tok2", "platform": "apns"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "updated"}

    list_resp = client.get("/users/device-tokens", headers=headers)
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["platform"] == "apns"


def test_register_device_token_reassigns_to_new_owner(client):
    alice_headers = _register(client, "alice")
    client.post("/users/device-token", json={"token": "shared-token", "platform": "fcm"}, headers=alice_headers)

    bob_headers = _register(client, "bob")
    resp = client.post("/users/device-token", json={"token": "shared-token", "platform": "fcm"}, headers=bob_headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "updated"}

    alice_tokens = client.get("/users/device-tokens", headers=alice_headers).json()
    bob_tokens = client.get("/users/device-tokens", headers=bob_headers).json()
    assert alice_tokens == []
    assert len(bob_tokens) == 1
    assert bob_tokens[0]["token"] == "shared-token"


def test_unregister_device_token(client):
    headers = _register(client, "carol")
    client.post("/users/device-token", json={"token": "tok3", "platform": "fcm"}, headers=headers)

    resp = client.delete("/users/device-token?token=tok3", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "unregistered"}

    assert client.get("/users/device-tokens", headers=headers).json() == []


def test_unregister_device_token_other_users_token_is_noop(client):
    alice_headers = _register(client, "alice")
    bob_headers = _register(client, "bob")
    client.post("/users/device-token", json={"token": "tok4", "platform": "fcm"}, headers=alice_headers)

    resp = client.delete("/users/device-token?token=tok4", headers=bob_headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "unregistered"}
    assert len(client.get("/users/device-tokens", headers=alice_headers).json()) == 1