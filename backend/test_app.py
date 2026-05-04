from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401 — registers Note + User on Base.metadata
from app import app, get_db

# ── In-memory test database (always fresh schema) ────────────────────────────

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=_test_engine)
Base.metadata.create_all(bind=_test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _signup_login(email: str, password: str = "testpass123") -> str:
    """Register a user and return a valid Bearer token."""
    client.post("/signup", json={"email": email, "password": password})
    res = client.post("/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth tests ────────────────────────────────────────────────────────────────

def test_signup_success():
    res = client.post("/signup", json={"email": "new@example.com", "password": "pass"})
    assert res.status_code == 201

def test_signup_duplicate():
    client.post("/signup", json={"email": "dup@example.com", "password": "pass"})
    res = client.post("/signup", json={"email": "dup@example.com", "password": "pass"})
    assert res.status_code == 400

def test_login_success():
    client.post("/signup", json={"email": "login@example.com", "password": "pass"})
    res = client.post("/login", json={"email": "login@example.com", "password": "pass"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_wrong_password():
    client.post("/signup", json={"email": "wp@example.com", "password": "correct"})
    res = client.post("/login", json={"email": "wp@example.com", "password": "wrong"})
    assert res.status_code == 401

def test_login_unknown_user():
    res = client.post("/login", json={"email": "nobody@example.com", "password": "x"})
    assert res.status_code == 401


# ── Protected-route tests ─────────────────────────────────────────────────────

def test_get_notes_unauthenticated():
    res = client.get("/notes")
    assert res.status_code in (401, 403)


def test_create_note_unauthenticated():
    res = client.post("/notes", json={"content": "hack"})
    assert res.status_code in (401, 403)

def test_create_and_get_notes():
    token = _signup_login("user1@example.com")
    res = client.post("/notes", json={"content": "hello"}, headers=auth(token))
    assert res.status_code == 201
    assert res.json()["content"] == "hello"

    res = client.get("/notes", headers=auth(token))
    assert res.status_code == 200
    assert any(n["content"] == "hello" for n in res.json())

def test_note_schema_validation():
    token = _signup_login("schema@example.com")
    res = client.post("/notes", json={}, headers=auth(token))
    assert res.status_code == 422


# ── Ownership tests ───────────────────────────────────────────────────────────

def test_notes_isolated_between_users():
    t1 = _signup_login("owner1@example.com")
    t2 = _signup_login("owner2@example.com")

    client.post("/notes", json={"content": "owner1 note"}, headers=auth(t1))

    notes_2 = client.get("/notes", headers=auth(t2)).json()
    assert not any(n["content"] == "owner1 note" for n in notes_2)

def test_cross_user_delete_blocked():
    t1 = _signup_login("del1@example.com")
    t2 = _signup_login("del2@example.com")

    note_id = client.post(
        "/notes", json={"content": "mine"}, headers=auth(t1)
    ).json()["id"]

    res = client.delete(f"/notes/{note_id}", headers=auth(t2))
    assert res.status_code == 404  # user2 cannot see user1's note

def test_delete_own_note():
    token = _signup_login("delown@example.com")
    note_id = client.post(
        "/notes", json={"content": "to delete"}, headers=auth(token)
    ).json()["id"]

    res = client.delete(f"/notes/{note_id}", headers=auth(token))
    assert res.status_code == 200