import sys
import os
import zipfile
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import ExtractedCard
from anki_builder import build_deck, _stable_note_id


SAMPLE_CARDS = [
    ExtractedCard(
        front="What are the chambers of the heart?",
        back="Two atria and two ventricles",
        tags=["Cardiology"],
    ),
    ExtractedCard(
        front="Define cardiac output",
        back="CO = HR x SV",
        tags=["Cardiology"],
    ),
]


def test_build_deck_returns_bytes():
    result = build_deck(SAMPLE_CARDS, "Test Deck")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_apkg_is_valid_zip():
    result = build_deck(SAMPLE_CARDS, "Test Deck")
    z = zipfile.ZipFile(io.BytesIO(result))
    names = z.namelist()
    assert "collection.anki2" in names or "collection.anki21" in names


def test_stable_ids_deterministic():
    id1 = _stable_note_id("What are the chambers of the heart?")
    id2 = _stable_note_id("What are the chambers of the heart?")
    assert id1 == id2


def test_different_questions_different_ids():
    id1 = _stable_note_id("Question one")
    id2 = _stable_note_id("Question two")
    assert id1 != id2


def test_empty_deck():
    result = build_deck([], "Empty Deck")
    assert isinstance(result, bytes)
    assert len(result) > 0
