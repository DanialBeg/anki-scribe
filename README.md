# Anki Scribe

Converts Google Docs study notes into Anki flashcard decks (.apkg).

Write your notes with bold questions and answers underneath. Anki Scribe picks them up, lets you review the cards, and exports a deck you can import straight into Anki.

## How it works

1. Open a Google Doc with your study notes
2. Click "Convert to Anki Cards" in the sidebar
3. Review, edit, or delete cards in the preview
4. Download the .apkg file and import into Anki

## Note format

Bold text is treated as the front of a card. Everything below it (until the next bold line or heading) becomes the back.

Section headings with color (e.g. purple titles) are applied as Anki tags to all cards in that section.

Tables and images in answers are included on the card.

```
PHARMACOLOGY                          <- heading, becomes a tag

What are the side effects of drug X?  <- bold, becomes front of card
- Nausea                              <- answer, becomes back of card
- Headache
- Dizziness
```

## Re-importing

Cards have stable IDs based on the question text. If you edit your notes and re-export, Anki will update existing cards rather than creating duplicates.

## Project structure

```
backend/     Python API (FastAPI + genanki) — parses notes and generates .apkg files
addon/       Google Docs add-on (Apps Script) — reads the doc and shows the UI
```

## Running the backend locally

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn genanki pydantic
uvicorn main:app --reload
```

## Tests

```
cd backend
pip install pytest httpx
pytest
```

## Deployment

The backend runs on any platform that supports Docker (Cloud Run, Railway, Render, etc.). The add-on is installed via Google Apps Script as a test deployment — no marketplace listing needed for personal use.
