import re
from typing import List, Optional

from models import ExtractedCard, Paragraph

ORANGE_COLORS = {"#ff6600", "#e69138", "#ff9900", "#f6b26b", "#ce7e00", "#ff8c00"}
PURPLE_COLORS = {"#800080", "#9900ff", "#674ea7", "#8e7cc3", "#7030a0", "#9933ff"}


def sanitize_tag(text: str) -> str:
    """Convert heading text to a valid Anki tag."""
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.title() if text else ""


def _get_heading_level(paragraph: Paragraph) -> Optional[int]:
    """Determine heading level: 1 = orange/top-level, 2 = purple/subsection, None = not a heading."""
    if paragraph.heading_level is not None:
        return paragraph.heading_level

    if not paragraph.text_color:
        if paragraph.is_heading:
            return 2
        return None

    color = paragraph.text_color.lower()
    if color in ("#000000", "black", "#000"):
        return None

    if color in ORANGE_COLORS:
        return 1
    if color in PURPLE_COLORS:
        return 2

    return 2


def _build_tag(level1: Optional[str], level2: Optional[str]) -> Optional[str]:
    """Build a nested tag string from level 1 and level 2 components."""
    if level1 and level2:
        return f"{level1}::{level2}"
    return level1 or level2 or None


def _save_card(
    question: str,
    answer_lines: list[str],
    answer_images: list[str],
    level1_tag: Optional[str],
    level2_tag: Optional[str],
    cards: list[ExtractedCard],
) -> None:
    """Append a completed card to the cards list."""
    if not question:
        return
    back = "\n".join(answer_lines).strip()
    tag = _build_tag(level1_tag, level2_tag)
    tags = [tag] if tag else []
    cards.append(ExtractedCard(front=question.strip(), back=back, tags=tags, images=answer_images))


def extract_cards(paragraphs: list[Paragraph]) -> list[ExtractedCard]:
    """Extract Q&A cards from a list of paragraphs using bold detection."""
    cards: list[ExtractedCard] = []
    level1_tag: Optional[str] = None
    level2_tag: Optional[str] = None
    current_question: Optional[str] = None
    current_answer_lines: list[str] = []
    current_images: list[str] = []

    for paragraph in paragraphs:
        text = paragraph.text.strip()

        if paragraph.is_table and paragraph.table_html:
            current_answer_lines.append(paragraph.table_html)
            current_images.extend(paragraph.images)
            continue

        if not text:
            if paragraph.images:
                current_images.extend(paragraph.images)
            continue

        heading_level = _get_heading_level(paragraph)

        if heading_level is not None:
            _save_card(current_question, current_answer_lines, current_images, level1_tag, level2_tag, cards)
            current_question = None
            current_answer_lines = []
            current_images = []

            tag_text = sanitize_tag(text)
            if heading_level == 1:
                level1_tag = tag_text
                level2_tag = None
            else:
                level2_tag = tag_text

        elif paragraph.is_bold:
            _save_card(current_question, current_answer_lines, current_images, level1_tag, level2_tag, cards)
            current_answer_lines = []
            current_images = []
            current_question = text

        else:
            current_answer_lines.append(text)
            current_images.extend(paragraph.images)

    _save_card(current_question, current_answer_lines, current_images, level1_tag, level2_tag, cards)

    return cards
