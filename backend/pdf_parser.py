"""Parse PDF files into Paragraph objects using PyMuPDF."""

import colorsys
import re

import fitz

from models import Paragraph

_BULLET_RE = re.compile(r"^(\d{1,2}[.)]\s|[-•·–—]\s)")
_LONE_BULLET_RE = re.compile(r"^[-•·–—]$|^\d{1,2}[.)]$")


def _rgb_to_hex(color: int) -> str:
    """Convert a PyMuPDF color integer to a hex string like #rrggbb."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def _is_bold_span(span: dict) -> bool:
    """Check if a text span is bold via flags or font name."""
    flags = span.get("flags", 0)
    if flags & 16:
        return True
    font = span.get("font", "").lower()
    return "bold" in font


def _detect_heading_color(hex_color: str) -> int | None:
    """Return heading level (1=orange, 2=purple) by matching hue range."""
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue = h * 360

    if s < 0.2 or v < 0.2:
        return None

    # Orange/red range: ~10-50 degrees
    if 10 <= hue <= 50:
        return 1
    # Purple/magenta range: ~270-330 degrees
    if 270 <= hue <= 330:
        return 2
    return None


def _line_to_paragraph(spans: list[dict]) -> Paragraph | None:
    """Convert a list of spans from one text line into a Paragraph."""
    text_parts = []
    all_bold = True
    colors = set()

    for span in spans:
        text = span.get("text", "")
        if not text.strip():
            continue
        if text_parts and text_parts[-1] and not text_parts[-1][-1].isspace() and not text[0].isspace():
            text_parts.append(" ")
        text_parts.append(text)
        if not _is_bold_span(span):
            all_bold = False
        colors.add(_rgb_to_hex(span.get("color", 0)))

    full_text = "".join(text_parts).strip()
    full_text = full_text.replace("\u200b", " ")
    full_text = re.sub(r" {2,}", " ", full_text)
    if not full_text:
        return None

    text_color = None
    heading_level = None
    is_heading = False

    non_black_colors = {c for c in colors if c not in ("#000000", "#000")}
    if non_black_colors:
        color = next(iter(non_black_colors))
        level = _detect_heading_color(color)
        if level is not None:
            text_color = color
            heading_level = level
            is_heading = True

    return Paragraph(
        text=full_text,
        is_bold=all_bold and not is_heading,
        is_heading=is_heading,
        text_color=text_color,
        heading_level=heading_level,
    )


def _merge_continuations(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """Merge PDF continuation lines back into their parent bullet/list items."""
    if not paragraphs:
        return paragraphs
    merged = [paragraphs[0]]
    for para in paragraphs[1:]:
        prev = merged[-1]
        if not para.text:
            merged.append(para)
            continue
        if (_LONE_BULLET_RE.match(prev.text)
                and not para.is_bold and not para.is_heading
                and not _LONE_BULLET_RE.match(para.text)):
            prev.text = prev.text + " " + para.text.lstrip()
            prev.is_bold = False
        elif (not para.is_bold and not para.is_heading
                and not prev.is_bold and not prev.is_heading
                and _BULLET_RE.match(prev.text)
                and not _BULLET_RE.match(para.text)
                and not _LONE_BULLET_RE.match(para.text)):
            prev.text = prev.text.rstrip() + " " + para.text.lstrip()
        elif (para.is_bold and prev.is_bold
                and para.text[0].islower()):
            prev.text = prev.text.rstrip() + " " + para.text.lstrip()
        else:
            merged.append(para)
    return merged


def _extract_images(page: fitz.Page) -> list[str]:
    """Extract embedded images from a page as base64 strings."""
    import base64

    images = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            pix = fitz.Pixmap(page.parent, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_bytes = pix.tobytes("png")
            images.append(base64.b64encode(img_bytes).decode("ascii"))
        except Exception:
            continue
    return images


def parse_pdf(pdf_bytes: bytes) -> list[Paragraph]:
    """Parse a PDF file into a list of Paragraph objects with formatting metadata."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    paragraphs: list[Paragraph] = []

    for page in doc:
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                para = _line_to_paragraph(spans)
                if para:
                    paragraphs.append(para)

        page_images = _extract_images(page)
        if page_images:
            paragraphs.append(Paragraph(text="", images=page_images))

    doc.close()
    return _merge_continuations(paragraphs)
