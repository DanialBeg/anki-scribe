from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models import ExtractRequest, ExtractResponse, GenerateRequest
from qa_parser import extract_cards
from anki_builder import build_deck
from pdf_parser import parse_pdf

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI(title="Docs to Anki")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://docs.google.com",
        "https://script.google.com",
        "https://danialbeg.com",
        "https://www.danialbeg.com",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/pdf-upload", response_model=ExtractResponse)
async def pdf_upload(file: UploadFile):
    """Accept a PDF upload, extract Q&A cards, and return them for preview."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 20 MB limit")

    paragraphs = parse_pdf(pdf_bytes)
    cards = extract_cards(paragraphs)
    return ExtractResponse(cards=cards)


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
