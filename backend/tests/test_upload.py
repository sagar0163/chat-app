import io
import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app, init_db, async_session

client = TestClient(app)

USERNAME = "uploaduser"
EMAIL = "upload@test.com"
PASSWORD = "testpass123"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    asyncio.run(init_db())
    yield


@pytest.fixture(scope="session")
def auth_token():
    client.post("/auth/register", json={
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
    })
    resp = client.post("/auth/login", json={"username": USERNAME, "password": PASSWORD})
    return resp.json()["access_token"]


def test_upload_valid_image(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    resp = client.post(
        "/upload",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"].startswith("/uploads/")
    assert data["url"].endswith(".png")
    assert data["content_type"] == "image/png"
    assert data["message_type"] == "image"
    assert data["size"] == len(image_bytes)


def test_upload_valid_pdf(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    pdf_bytes = b"%PDF-1.4" + b"\x00" * 100
    resp = client.post(
        "/upload",
        files={"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("/uploads/")
    assert resp.json()["message_type"] == "file"


def test_upload_disallowed_type(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    exe_bytes = b"\x00" * 100
    resp = client.post(
        "/upload",
        files={"file": ("malware.exe", io.BytesIO(exe_bytes), "application/octet-stream")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]


def test_upload_image_too_large(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    big_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        "/upload",
        files={"file": ("big.png", io.BytesIO(big_image), "image/png")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "5MB" in resp.json()["detail"]


def test_upload_file_too_large(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    big_pdf = b"%PDF-1.4" + b"\x00" * (10 * 1024 * 1024 + 1)
    resp = client.post(
        "/upload",
        files={"file": ("big.pdf", io.BytesIO(big_pdf), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "10MB" in resp.json()["detail"]


def test_upload_ignores_client_extension_and_traversal(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post(
        "/upload",
        files={"file": ("../../evil.html", io.BytesIO(b"<script>x</script>"), "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 200
    url = resp.json()["url"]
    assert url.startswith("/uploads/")
    assert url.endswith(".txt")
    assert ".." not in url
    assert "html" not in url


def test_upload_requires_auth():
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
    resp = client.post(
        "/upload",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert resp.status_code == 403


def test_upload_file_is_saved_to_disk(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    content = b"hello upload test"
    resp = client.post(
        "/upload",
        files={"file": ("hello.txt", io.BytesIO(content), "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 200
    url = resp.json()["url"]
    filename = url.split("/")[-1]
    filepath = os.path.join("uploads", filename)
    assert os.path.exists(filepath)
    with open(filepath, "rb") as f:
        assert f.read() == content