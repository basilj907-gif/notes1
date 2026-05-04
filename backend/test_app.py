from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_create_note():
    response = client.post("/notes", params={"content": "test note"})
    assert response.status_code == 200
    assert response.json()["content"] == "test note"

def test_get_notes():
    response = client.get("/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_note():
    create = client.post("/notes", params={"content": "to delete"})
    note_id = create.json()["id"]

    delete = client.delete(f"/notes/{note_id}")
    assert delete.status_code == 200

def test_invalid_note():
    response = client.post("/notes", json={})
    assert response.status_code == 422