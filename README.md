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
set FLASK_APP=app.py
flask db upgrade            # creates instance/puzzles.db (sqlite) locally
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
- `config.py`, `extensions.py`, `models.py` — Flask config, SQLAlchemy/Migrate
  instances, and the `Puzzle` model (persists generated puzzles so PDF
  download never needs to re-run the LLM call, and survives restarts)
- `migrations/` — Alembic migration scripts (`flask db migrate` / `upgrade`)
- `templates/`, `static/` — frontend

Database: defaults to a local `instance/puzzles.db` SQLite file if
`DATABASE_URL` isn't set. Render provides `DATABASE_URL` automatically
from the attached Postgres instance in production.

## Deploy (Render)

This repo includes a `render.yaml` blueprint targeting Render's free web
service tier:

1. Push this repo to GitHub (already done if you're reading this from
   `rspahn-dev/puzzle-forge`).
2. In the [Render dashboard](https://dashboard.render.com), choose
   **New → Blueprint** and select the `puzzle-forge` repo.
3. Render also reads the `databases:` block and provisions a free
   Postgres instance, wiring its connection string into the web
   service's `DATABASE_URL` automatically — no manual step needed there.
4. Render prompts you for the one secret it doesn't get from git:
   `ANTHROPIC_API_KEY`. Paste it in (optional — the app works fine
   without it, using the offline word bank).
5. Deploy. Render builds with
   `pip install -r requirements.txt && flask db upgrade` (applying any
   pending migrations) and runs
   `gunicorn wsgi:app --workers 1 --bind 0.0.0.0:$PORT`.
6. Visit the assigned `*.onrender.com` URL.

Notes:
- Free tier spins down after ~15 min idle; the next request takes ~30s to
  wake it back up. Fine for low-traffic use; upgrade to a paid plan later
  for always-on if needed.
- Render's free Postgres instances expire after 90 days and need
  recreating (or upgrading to a paid plan) — a known limitation of the
  free tier, not something this app can work around.
- `--workers 1` is a deliberate choice for now — future phases (auth,
  session-heavy features) haven't been load-tested beyond a single
  worker yet.

## Notes / next steps

- Each `/generate` call costs a small amount against the Anthropic API key —
  worth adding rate limiting before making this public.
- KDP/Etsy book angle: PDF export is per-puzzle today; a batch mode that
  generates N puzzles across a theme list into one bound PDF would be the
  next step for turning this into a sellable puzzle book.
