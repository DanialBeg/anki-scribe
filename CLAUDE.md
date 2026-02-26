# Docs → Anki

A Google Docs add-on that converts study notes into Anki flashcards. Built for a non-technical medical student.

## Project Overview

- **User**: Medical student who writes Q&A study notes in Google Docs with bold questions and answers below
- **Goal**: Automate the copy-paste of Q&A pairs into Anki flashcard decks (.apkg files)
- **Interface**: Google Workspace Add-on (sidebar in Google Docs) → cloud backend → .apkg download
- **Card type**: Simple front/back only. No cloze deletions.

## Architecture

```
Google Docs Add-on (Apps Script) → Cloud Backend (Python/FastAPI) → .apkg file
```

- `addon/` — Google Apps Script add-on (reads doc, shows preview, triggers download)
- `backend/` — Python FastAPI service (parses Q&A pairs, generates .apkg)
- `plan/plan.md` — Full project plan with implementation details

## Note Format (How the user writes)

- **Bold text** = question (becomes card front)
- **Non-bold text below** = answer (becomes card back)
- **Colored/purple headings** = section titles (become Anki tags on all cards in that section)
- A paragraph is only a "question" if the **entire paragraph** is bold (partial bold like mnemonic letters is still an answer)

## Parsing Rules

The parser is **rule-based** (no AI). The algorithm walks paragraphs sequentially:
1. Colored heading or doc heading → set as current tag (sanitized: "TREATMENT OF BIPOLAR DISORDER" → `Treatment-of-Bipolar-Disorder`)
2. Fully bold paragraph → start a new card (this is the front)
3. Non-bold paragraph → append to current card's back
4. Each card inherits the most recent section heading as its tag

## Key Design Decisions

- **Stable card IDs**: Note IDs are deterministic hashes of the question text, so re-importing an updated .apkg updates existing cards instead of creating duplicates
- **No AnkiConnect**: The user downloads .apkg and imports into Anki manually (double-click). Simplest approach for a non-technical user.
- **No AI for v1**: The note format is consistent enough that rule-based bold detection works. AI can be added later for messy/inconsistent notes.
- **Full-paragraph bold detection**: Only paragraphs where ALL text is bold are treated as questions. Partially bold paragraphs (e.g., mnemonic first letters) remain part of the answer.

## Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Key libraries**: `genanki` (Anki deck generation), `pydantic` (data validation)
- **Deployment target**: Google Cloud Run (Dockerfile provided)

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/extract` | POST | Receive paragraphs with formatting → return extracted cards for preview |
| `/api/generate` | POST | Receive approved cards → return .apkg file download |

### Backend Files

| File | Purpose |
|------|---------|
| `models.py` | Pydantic schemas: Paragraph, ExtractedCard, ExtractRequest, GenerateRequest |
| `qa_parser.py` | Rule-based Q&A extraction from paragraphs (bold detection + heading → tags) |
| `anki_builder.py` | Generates .apkg using genanki (front/back cards, tags, stable IDs) |
| `main.py` | FastAPI app with routes and CORS config |

## Add-on (Google Apps Script)

| File | Purpose |
|------|---------|
| `appsscript.json` | Manifest with scopes and add-on config |
| `Code.gs` | Server-side: reads doc content, calls backend API |
| `Sidebar.html` | Main sidebar UI with "Convert to Anki" button |
| `CardReview.html` | Card preview/edit dialog (~700x500px) |
| `styles.css.html` | Shared CSS |

## Development Commands

```bash
# Backend
cd backend
pip install -e ".[dev]"           # Install with dev dependencies
uvicorn main:app --reload         # Run locally
pytest                            # Run tests

# Docker
docker build -t docs-anki .       # Build image
docker run -p 8000:8000 docs-anki # Run container
```

## Testing

- Run `pytest` from `backend/` directory
- The bipolar disorder example (from plan/plan.md) should produce exactly **11 cards**, all tagged `Treatment-of-Bipolar-Disorder`
- Tests cover: parser correctness, edge cases (empty docs, consecutive headings, partial bold), stable ID generation, .apkg validity

## Conventions

- Keep it simple — this is a focused tool, not a framework
- No unnecessary abstractions or over-engineering
- Backend modules expose single main functions (`extract_cards()`, `build_deck()`)
- All card styling CSS lives in `anki_builder.py` (embedded in the genanki model)
- Error messages should be user-friendly (the end user is non-technical)
- **Comments**: Minimal. Only add docstrings on function declarations and comments where logic is genuinely non-obvious. No inline narration.
- **Commits**: One concise sentence per commit message. No bullet points, no multi-line descriptions.
