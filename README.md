# Anki Scribe

Converts study notes into Anki flashcard decks (.apkg).

Write your notes with bold questions and answers underneath. Anki Scribe picks them up, lets you review the cards, and exports a deck you can import straight into Anki.

## How it works

**Web UI** — upload a PDF at [anki-scribe.vercel.app](https://anki-scribe.vercel.app), preview the extracted cards, then download the .apkg file.

**Google Docs add-on** — convert notes directly from a Google Doc sidebar.

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
frontend/    Web UI (React + Vite + TypeScript) — PDF upload, card preview, .apkg download
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

| Component | Platform |
|-----------|----------|
| Backend | Google Cloud Run (auto-deploys from `main` via Cloud Build) |
| Frontend | Vercel at [anki-scribe.vercel.app](https://anki-scribe.vercel.app) (auto-deploys from `main`, root directory: `frontend/`) |
| Add-on | Google Apps Script (test deployment, personal use) |

The frontend reads `VITE_API_URL` to know where the backend lives (set as an env var in Vercel).
