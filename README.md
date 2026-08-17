# Puzzle Forge

Currently: type a theme, get a word search puzzle. The grid is placed by
a local algorithm, and the result can be played on-screen or downloaded
as a print-ready PDF (puzzle page + answer key page).

This is growing into a multi-game puzzle platform (crossword, sudoku,
word scramble, user accounts with per-user API keys) — word search is
the first game type, built out first so the deploy pipeline and core
patterns exist before the rest gets layered on.

Word lists come from one of two sources:

- **No API key configured** (default): a built-in word bank covering ~15
  common themes (animals, ocean, space, sports, food, holidays, etc.),
  plus a generic fallback for anything else. Works immediately, no setup.
- **`ANTHROPIC_API_KEY` set in `.env`**: word lists are generated live by
  Claude for *any* typed theme. Falls back to the offline bank automatically
  if the API call fails for any reason.

The UI shows a small note whenever a puzzle used the offline bank instead
of live generation.

## Setup

```
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Optional, for AI-generated word lists on any theme:

```
copy .env.example .env      # then fill in ANTHROPIC_API_KEY
```

## Run

```
python app.py
```

Then open http://127.0.0.1:5000

## Project structure

- `wordsearch/generator.py` — grid placement algorithm (pure Python, no deps)
- `wordsearch/themes.py` — calls the Anthropic API to turn a theme into a word list
- `wordsearch/pdf_export.py` — renders a puzzle to a print-ready PDF via reportlab
- `app.py` — Flask routes: `/` (form), `/generate` (JSON API), `/download/<id>.pdf`
- `templates/`, `static/` — frontend

## Deploy (Render)

This repo includes a `render.yaml` blueprint targeting Render's free web
service tier:

1. Push this repo to GitHub (already done if you're reading this from
   `rspahn-dev/puzzle-forge`).
2. In the [Render dashboard](https://dashboard.render.com), choose
   **New → Blueprint** and select the `puzzle-forge` repo.
3. Render reads `render.yaml` and prompts you for the one secret it
   doesn't get from git: `ANTHROPIC_API_KEY`. Paste it in (optional — the
   app works fine without it, using the offline word bank).
4. Deploy. Render builds with `pip install -r requirements.txt` and runs
   `gunicorn wsgi:app --workers 1 --bind 0.0.0.0:$PORT`.
5. Visit the assigned `*.onrender.com` URL.

Notes:
- Free tier spins down after ~15 min idle; the next request takes ~30s to
  wake it back up. Fine for low-traffic use; upgrade to a paid plan later
  for always-on if needed.
- `--workers 1` is required as long as puzzles live in the in-memory
  store below — multiple workers would each have their own copy and
  `/download/<id>.pdf` would 404 depending which worker handled it.

## Notes / next steps

- Puzzles are kept in an in-memory dict keyed by UUID so the PDF download
  doesn't need to re-run the LLM call. Fine for local/single-process use;
  would need a real store (DB, Redis, or signed puzzle-in-URL) before
  deploying with multiple workers.
- Each `/generate` call costs a small amount against the Anthropic API key —
  worth adding rate limiting before making this public.
- KDP/Etsy book angle: PDF export is per-puzzle today; a batch mode that
  generates N puzzles across a theme list into one bound PDF would be the
  next step for turning this into a sellable puzzle book.
