from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models import ExtractRequest, ExtractResponse, GenerateRequest
from qa_parser import extract_cards
from anki_builder import build_deck

app = FastAPI(title="Docs to Anki")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://docs.google.com", "https://script.google.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract", response_model=ExtractResponse)
def extract(request: ExtractRequest):
    """Parse paragraphs and return extracted Q&A cards for preview."""
    cards = extract_cards(request.paragraphs)
    return ExtractResponse(cards=cards)


@app.post("/api/generate")
def generate(request: GenerateRequest):
    """Generate an .apkg file from approved cards."""
    apkg_bytes = build_deck(request.cards, request.deck_name)
    return Response(
        content=apkg_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{request.deck_name}.apkg"'},
    )
