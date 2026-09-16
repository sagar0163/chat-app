"""Tests for Issue #6: prevent unauthorized adding of users to chats.

Group chats now use an invite flow: members listed at creation time are only
pending invitees; they become members when they accept the invite. Direct
messages still add the other user directly.
"""
import os
import tempfile
from uuid import uuid4

TEST_DB = os.path.join(tempfile.gettempdir(), f"chat_app_test_issue6_{uuid4().hex[:8]}.db")
for suffix in ("", "-wal", "-shm"):
    if os.path.exists(TEST_DB + suffix):
        os.remove(TEST_DB + suffix)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"

import pytest
from fastapi.testclient import TestClient

from main import app, limiter

limiter.enabled = False


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(TEST_DB + suffix):
            os.remove(TEST_DB + suffix)


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
    token = login(client, name)
    return user, token


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def create_group_chat(client, token, member_ids, name=None):
    return client.post(
        "/chats",
        json={"name": name, "is_group": True, "member_ids": member_ids},
        headers=bearer(token),
    )


def test_group_chat_membership_requires_accepted_invite(client):
    alice, alice_token = new_user(client)
    bob, bob_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"]])
    assert resp.status_code == 200, resp.text
    chat = resp.json()
    chat_id = chat["id"]

    member_ids = [m["id"] for m in chat["members"]]
    assert member_ids == [alice["id"]], "creator is the only active member before invite is accepted"
    assert bob["id"] not in member_ids

    bob_chats = client.get("/chats", headers=bearer(bob_token)).json()
    assert all(c["id"] != chat_id for c in bob_chats), "invitee must not see chat before accepting"

    forbidden = client.get(f"/chats/{chat_id}", headers=bearer(bob_token))
    assert forbidden.status_code == 403

    invites = client.get("/invites", headers=bearer(bob_token)).json()
    assert len(invites) == 1
    invite = invites[0]
    assert invite["chat_id"] == chat_id
    assert invite["invitee_id"] == bob["id"]
    assert invite["inviter_id"] == alice["id"]
    assert invite["status"] == "pending"

    accepted = client.post(f"/invites/{invite['id']}/accept", headers=bearer(bob_token))
    assert accepted.status_code == 200
    assert accepted.json() == {"status": "accepted"}

    bob_chats = client.get("/chats", headers=bearer(bob_token)).json()
    assert any(c["id"] == chat_id for c in bob_chats), "accepted invitee appears in chat list"

    detail = client.get(f"/chats/{chat_id}", headers=bearer(bob_token))
    assert detail.status_code == 200
    assert {m["id"] for m in detail.json()["members"]} == {alice["id"], bob["id"]}


def test_bob_cannot_access_group_chat_messages_before_accepting(client):
    alice, alice_token = new_user(client)
    bob, bob_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"]], name="top secret")
    chat_id = resp.json()["id"]

    messages = client.get(f"/chats/{chat_id}/messages", headers=bearer(bob_token))
    assert messages.status_code == 403


def test_invite_cannot_be_accepted_by_another_user(client):
    _, alice_token = new_user(client)
    bob, bob_token = new_user(client)
    carol, carol_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"]])
    chat_id = resp.json()["id"]

    invites = client.get("/invites", headers=bearer(bob_token)).json()
    invite_id = invites[0]["id"]

    denied = client.post(f"/invites/{invite_id}/accept", headers=bearer(carol_token))
    assert denied.status_code == 404

    carol_view = client.get(f"/chats/{chat_id}", headers=bearer(carol_token))
    assert carol_view.status_code == 403


def test_rejected_invite_does_not_grant_membership(client):
    alice, alice_token = new_user(client)
    bob, bob_token = new_user(client)
    dave, dave_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"], dave["id"]])
    chat_id = resp.json()["id"]

    bob_invites = client.get("/invites", headers=bearer(bob_token)).json()
    bob_invite = next(i for i in bob_invites if i["invitee_id"] == bob["id"])
    rejected = client.post(f"/invites/{bob_invite['id']}/reject", headers=bearer(bob_token))
    assert rejected.status_code == 200
    assert rejected.json() == {"status": "rejected"}

    bob_chats = client.get("/chats", headers=bearer(bob_token)).json()
    assert all(c["id"] != chat_id for c in bob_chats)
    assert client.get(f"/chats/{chat_id}", headers=bearer(bob_token)).status_code == 403

    # A rejected invite can no longer be accepted by the owner
    again = client.post(f"/invites/{bob_invite['id']}/accept", headers=bearer(bob_token))
    assert again.status_code == 404


def test_accept_invite_twice_is_idempotent_and_no_duplicate_membership(client):
    alice, alice_token = new_user(client)
    bob, bob_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"]])
    chat_id = resp.json()["id"]

    invite_id = client.get("/invites", headers=bearer(bob_token)).json()[0]["id"]
    assert client.post(f"/invites/{invite_id}/accept", headers=bearer(bob_token)).status_code == 200
    # Second accept must not create duplicate membership
    assert client.post(f"/invites/{invite_id}/accept", headers=bearer(bob_token)).status_code == 404

    detail = client.get(f"/chats/{chat_id}", headers=bearer(alice_token)).json()
    ids = [m["id"] for m in detail["members"]]
    assert ids.count(bob["id"]) == 1


def test_create_group_with_unknown_member_is_rejected(client):
    alice, alice_token = new_user(client)
    resp = create_group_chat(client, alice_token, [999999])
    assert resp.status_code == 400
    assert "Unknown user" in resp.json()["detail"]


def test_duplicate_member_ids_create_single_invite(client):
    _, alice_token = new_user(client)
    bob, bob_token = new_user(client)

    resp = create_group_chat(client, alice_token, [bob["id"], bob["id"]])
    assert resp.status_code == 200

    invites = client.get("/invites", headers=bearer(bob_token)).json()
    assert len(invites) == 1


def test_direct_message_adds_member_immediately(client):
    alice, alice_token = new_user(client)
    bob, bob_token = new_user(client)

    resp = client.post(
        "/chats",
        json={"is_group": False, "member_ids": [bob["id"]]},
        headers=bearer(alice_token),
    )
    assert resp.status_code == 200
    chat_id = resp.json()["id"]

    member_ids = [m["id"] for m in resp.json()["members"]]
    assert bob["id"] in member_ids

    bob_chats = client.get("/chats", headers=bearer(bob_token)).json()
    assert any(c["id"] == chat_id for c in bob_chats)

    invites = client.get("/invites", headers=bearer(bob_token)).json()
    assert len(invites) == 0