import re

from models import ExtractedCard, Paragraph


def sanitize_tag(text: str) -> str:
    """Convert heading text to a valid Anki tag."""
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.title() if text else ""


def _is_heading_or_colored(paragraph: Paragraph) -> bool:
    """Check if a paragraph is a section heading (by style or text color)."""
    if paragraph.is_heading:
        return True
    if paragraph.text_color and paragraph.text_color.lower() not in ("#000000", "black", "#000"):
        return True
    return False


def _save_card(
    question: str,
    answer_lines: list[str],
    answer_images: list[str],
    current_tag: str | None,
    cards: list[ExtractedCard],
) -> None:
    """Append a completed card to the cards list."""
    if not question:
        return
    back = "\n".join(answer_lines).strip()
    tags = [current_tag] if current_tag else []
    cards.append(ExtractedCard(front=question.strip(), back=back, tags=tags, images=answer_images))


def extract_cards(paragraphs: list[Paragraph]) -> list[ExtractedCard]:
    """Extract Q&A cards from a list of paragraphs using bold detection."""
    cards: list[ExtractedCard] = []
    current_tag: str | None = None
    current_question: str | None = None
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

        if _is_heading_or_colored(paragraph):
            _save_card(current_question, current_answer_lines, current_images, current_tag, cards)
            current_question = None
            current_answer_lines = []
            current_images = []
            current_tag = sanitize_tag(text)

        elif paragraph.is_bold:
            _save_card(current_question, current_answer_lines, current_images, current_tag, cards)
            current_answer_lines = []
            current_images = []
            current_question = text

        else:
            current_answer_lines.append(text)
            current_images.extend(paragraph.images)

    _save_card(current_question, current_answer_lines, current_images, current_tag, cards)

    return cards
