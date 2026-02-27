import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fitz

from pdf_parser import parse_pdf


def _make_pdf(blocks):
    """Create a PDF with text blocks. Each block is (text, fontname, fontsize, color, position).
    color is an RGB tuple like (1, 0, 0) for red."""
    doc = fitz.open()
    page = doc.new_page()

    y = 72
    for text, fontname, fontsize, color, bold in blocks:
        if bold and fontname == "helv":
            fontname = "hebo"
        point = fitz.Point(72, y)
        page.insert_text(point, text, fontname=fontname, fontsize=fontsize, color=color)
        y += fontsize + 8

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_bold_detection():
    pdf_bytes = _make_pdf([
        ("What is X?", "hebo", 12, (0, 0, 0), True),
        ("X is a thing", "helv", 12, (0, 0, 0), False),
    ])
    paragraphs = parse_pdf(pdf_bytes)
    assert len(paragraphs) >= 2

    bold_paras = [p for p in paragraphs if p.is_bold]
    non_bold_paras = [p for p in paragraphs if not p.is_bold and p.text.strip()]
    assert len(bold_paras) >= 1
    assert bold_paras[0].text == "What is X?"
    assert len(non_bold_paras) >= 1
    assert non_bold_paras[0].text == "X is a thing"


def test_colored_heading_purple():
    purple = (128 / 255, 0, 128 / 255)
    pdf_bytes = _make_pdf([
        ("MY TOPIC", "helv", 14, purple, False),
        ("Question?", "hebo", 12, (0, 0, 0), True),
        ("Answer here", "helv", 12, (0, 0, 0), False),
    ])
    paragraphs = parse_pdf(pdf_bytes)
    heading_paras = [p for p in paragraphs if p.is_heading]
    assert len(heading_paras) >= 1
    assert heading_paras[0].text == "MY TOPIC"
    assert heading_paras[0].heading_level == 2


def test_colored_heading_orange():
    orange = (1, 102 / 255, 0)
    pdf_bytes = _make_pdf([
        ("MAIN TOPIC", "helv", 14, orange, False),
        ("Q?", "hebo", 12, (0, 0, 0), True),
        ("A", "helv", 12, (0, 0, 0), False),
    ])
    paragraphs = parse_pdf(pdf_bytes)
    heading_paras = [p for p in paragraphs if p.is_heading]
    assert len(heading_paras) >= 1
    assert heading_paras[0].heading_level == 1


def test_empty_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    paragraphs = parse_pdf(pdf_bytes)
    assert paragraphs == []


def test_black_text_not_heading():
    pdf_bytes = _make_pdf([
        ("Not a heading", "helv", 12, (0, 0, 0), False),
        ("Q?", "hebo", 12, (0, 0, 0), True),
        ("A", "helv", 12, (0, 0, 0), False),
    ])
    paragraphs = parse_pdf(pdf_bytes)
    heading_paras = [p for p in paragraphs if p.is_heading]
    assert len(heading_paras) == 0


def test_end_to_end_with_qa_parser():
    """Verify PDF paragraphs feed correctly into the QA parser."""
    from qa_parser import extract_cards

    purple = (128 / 255, 0, 128 / 255)
    pdf_bytes = _make_pdf([
        ("PHARMACOLOGY", "helv", 14, purple, False),
        ("What is aspirin?", "hebo", 12, (0, 0, 0), True),
        ("A painkiller", "helv", 12, (0, 0, 0), False),
        ("What is ibuprofen?", "hebo", 12, (0, 0, 0), True),
        ("An NSAID", "helv", 12, (0, 0, 0), False),
    ])
    paragraphs = parse_pdf(pdf_bytes)
    cards = extract_cards(paragraphs)
    assert len(cards) == 2
    assert cards[0].front == "What is aspirin?"
    assert cards[0].back == "A painkiller"
    assert "Pharmacology" in cards[0].tags
    assert cards[1].front == "What is ibuprofen?"
