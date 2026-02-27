import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fitz
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _make_simple_pdf():
    """Create a minimal PDF with one bold question and one answer."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), "What is X?", fontname="hebo", fontsize=12)
    page.insert_text(fitz.Point(72, 92), "X is a thing", fontname="helv", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_upload_success():
    pdf_bytes = _make_simple_pdf()
    response = client.post(
        "/api/pdf-upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) >= 1
    assert data["cards"][0]["front"] == "What is X?"


def test_pdf_upload_invalid_type():
    response = client.post(
        "/api/pdf-upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_pdf_upload_empty_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    response = client.post(
        "/api/pdf-upload",
        files={"file": ("empty.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["cards"] == []
