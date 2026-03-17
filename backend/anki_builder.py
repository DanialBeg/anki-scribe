import base64
import hashlib
import os
import re
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
ul, ol {
    margin: 4px 0;
    padding-left: 24px;
}
li {
    margin: 2px 0;
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


_UL_RE = re.compile(r"^[-•·–—]\s+(.*)")
_OL_RE = re.compile(r"^\d{1,2}[.)]\s+(.*)")


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _text_to_html(text: str) -> str:
    """Convert plain text with newlines to HTML with proper list formatting."""
    text = text.replace("\u200b", " ")
    text = re.sub(r" {2,}", " ", text)
    lines = text.split("\n")
    html_parts = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith("<table") or stripped.startswith("<img"):
            html_parts.append(stripped)
            i += 1
            continue

        if _UL_RE.match(stripped):
            items = []
            while i < len(lines):
                s = lines[i].strip()
                m = _UL_RE.match(s) if s else None
                if not m:
                    break
                items.append(f"<li>{_escape_html(m.group(1))}</li>")
                i += 1
            html_parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        if _OL_RE.match(stripped):
            items = []
            while i < len(lines):
                s = lines[i].strip()
                m = _OL_RE.match(s) if s else None
                if not m:
                    break
                items.append(f"<li>{_escape_html(m.group(1))}</li>")
                i += 1
            html_parts.append(f"<ol>{''.join(items)}</ol>")
            continue

        html_parts.append(_escape_html(stripped))
        i += 1

    return "<br>".join(html_parts)


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
