from pydantic import BaseModel


class Paragraph(BaseModel):
    """A single paragraph from the document with formatting metadata."""
    text: str
    is_bold: bool = False
    is_heading: bool = False
    text_color: str | None = None
    is_table: bool = False
    table_html: str | None = None
    images: list[str] = []


class ExtractedCard(BaseModel):
    """A single Anki card extracted from the document."""
    front: str
    back: str
    tags: list[str] = []
    images: list[str] = []


class ExtractRequest(BaseModel):
    """Request body for the /api/extract endpoint."""
    paragraphs: list[Paragraph]


class ExtractResponse(BaseModel):
    """Response body for the /api/extract endpoint."""
    cards: list[ExtractedCard]


class GenerateRequest(BaseModel):
    """Request body for the /api/generate endpoint."""
    cards: list[ExtractedCard]
    deck_name: str = "My Deck"
