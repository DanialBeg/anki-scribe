from typing import List, Optional

from pydantic import BaseModel


class Paragraph(BaseModel):
    """A single paragraph from the document with formatting metadata."""
    text: str
    is_bold: bool = False
    is_heading: bool = False
    text_color: Optional[str] = None
    heading_level: Optional[int] = None
    is_table: bool = False
    table_html: Optional[str] = None
    images: List[str] = []


class ExtractedCard(BaseModel):
    """A single Anki card extracted from the document."""
    front: str
    back: str
    tags: List[str] = []
    images: List[str] = []


class ExtractRequest(BaseModel):
    """Request body for the /api/extract endpoint."""
    paragraphs: List[Paragraph]


class ExtractResponse(BaseModel):
    """Response body for the /api/extract endpoint."""
    cards: List[ExtractedCard]


class GenerateRequest(BaseModel):
    """Request body for the /api/generate endpoint."""
    cards: List[ExtractedCard]
    deck_name: str = "My Deck"
