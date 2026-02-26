import sys
import os
import zipfile
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract():
    payload = {
        "paragraphs": [
            {"text": "MY TOPIC", "is_bold": False, "is_heading": True, "text_color": "#800080"},
            {"text": "What is X?", "is_bold": True, "is_heading": False, "text_color": None},
            {"text": "X is a thing", "is_bold": False, "is_heading": False, "text_color": None},
        ]
    }
    response = client.post("/api/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 1
    assert data["cards"][0]["front"] == "What is X?"
    assert data["cards"][0]["back"] == "X is a thing"
    assert "My-Topic" in data["cards"][0]["tags"]


def test_generate():
    payload = {
        "cards": [
            {"front": "Q1?", "back": "A1", "tags": ["Test"]},
            {"front": "Q2?", "back": "A2", "tags": ["Test"]},
        ],
        "deck_name": "Test Deck"
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    z = zipfile.ZipFile(io.BytesIO(response.content))
    names = z.namelist()
    assert "collection.anki2" in names or "collection.anki21" in names


def test_extract_empty():
    payload = {"paragraphs": []}
    response = client.post("/api/extract", json=payload)
    assert response.status_code == 200
    assert response.json()["cards"] == []
