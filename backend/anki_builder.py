import base64
import hashlib
import os
import tempfile

import genanki

from models import ExtractedCard

CARD_CSS = """
.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 18px;
    text-align: left;
    color: #1a1a1a;
    background-color: #ffffff;
    padding: 20px;
    line-height: 1.5;
}
table {
    border-collapse: collapse;
    margin: 8px 0;
    width: 100%;
}
td, th {
    border: 1px solid #dadce0;
    padding: 6px 10px;
    text-align: left;
    font-size: 16px;
}
th {
    background: #f8f9fa;
    font-weight: 600;
}
img {
    max-width: 100%;
    height: auto;
    margin: 8px 0;
}
"""

MODEL = genanki.Model(
    1607392319,
    "Docs to Anki - Basic",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
        }
    ],
    css=CARD_CSS,
)


def _stable_note_id(text: str) -> int:
    """Generate a deterministic note ID from question text."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _text_to_html(text: str) -> str:
    """Convert plain text with newlines to HTML, preserving any existing HTML tags (tables, images)."""
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<table") or stripped.startswith("<img"):
            html_lines.append(stripped)
        else:
            stripped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(stripped)
    return "<br>".join(html_lines)


def _tag_to_subdeck(tag: str) -> str:
    """Convert a tag like 'Topic-A::Sub-B' to a readable subdeck name like 'Topic A::Sub B'."""
    return "::".join(part.replace("-", " ") for part in tag.split("::"))


def build_deck(cards: list[ExtractedCard], deck_name: str = "My Deck") -> bytes:
    """Build an .apkg file from a list of extracted cards, using tags as subdecks."""
    decks: dict[str, genanki.Deck] = {}
    media_files = []
    tmpdir = tempfile.mkdtemp()

    for card in cards:
        if card.tags:
            subdeck_suffix = _tag_to_subdeck(card.tags[0])
            full_name = f"{deck_name}::{subdeck_suffix}"
        else:
            full_name = deck_name

        if full_name not in decks:
            decks[full_name] = genanki.Deck(_stable_note_id(full_name), full_name)

        back_html = _text_to_html(card.back)

        for i, img_b64 in enumerate(card.images):
            filename = f"img_{hashlib.md5(img_b64[:100].encode()).hexdigest()[:12]}_{i}.png"
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_b64))
            media_files.append(filepath)
            back_html += f'<br><img src="{filename}">'

        note = genanki.Note(
            model=MODEL,
            fields=[_text_to_html(card.front), back_html],
            tags=card.tags,
            guid=genanki.guid_for(card.front),
        )
        decks[full_name].add_note(note)

    package = genanki.Package(list(decks.values()))
    if media_files:
        package.media_files = media_files

    with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as tmp:
        package.write_to_file(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
