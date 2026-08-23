# Puzzle Forge

Type a theme, get a puzzle — or for sudoku, just pick a difficulty.
Three game types live so far: word search (grid placed by a local
algorithm), word scramble (jumbled letters to unscramble), and sudoku
(generated with a guaranteed unique solution). All three can be played
on-screen or downloaded as a print-ready PDF (puzzle page + answer key
page).

This is growing into a multi-game puzzle platform (crossword, user
accounts with per-user API keys) — word search was the first game
type, built out first so the deploy pipeline and core patterns exist;
word scramble followed the same pattern. Sudoku doesn't use the
theme/word-list pipeline at all — it's pure local grid generation, no
LLM involved.

Word lists come from one of two sources:

- **Anonymous, or signed in with no key saved** (default): a built-in
  word bank covering ~15 common themes (animals, ocean, space, sports,
  food, holidays, etc.), plus a generic fallback for anything else. Works
  immediately, no setup, no cost to anyone.
- **Signed in with Google + an Anthropic API key saved in Account**: word
  lists are generated live by Claude for *any* typed theme, billed to
  *that user's own key* (stored encrypted, never the site owner's).
  Falls back to the offline bank automatically if the API call fails.

The UI shows a small note whenever a puzzle used the offline bank instead
of live generation. Only signed-in users with a saved key can trigger a
paid LLM call — anonymous visitors always get the offline path.

## Setup

```
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
set FLASK_APP=app.py
flask db upgrade            # creates instance/puzzles.db (sqlite) locally
```

Copy `.env.example` to `.env` and fill in secrets as needed — see below
for what each one is for. `SECRET_KEY` and `APP_ENCRYPTION_KEY` need real
values even locally (Flask sessions and API-key encryption both require
them); the rest are optional depending on what you're testing.

## Google sign-in setup

Sign-in and per-user API keys need a Google OAuth client:

1. [console.cloud.google.com](https://console.cloud.google.com) → APIs &
   Services → Credentials → **Create Credentials → OAuth client ID** →
   Application type **Web application**.
2. Add these as **Authorized redirect URIs**:
   - `http://127.0.0.1:5000/auth/callback` (local dev)
   - `https://<your-render-url>/auth/callback` (production)
3. Copy the Client ID and Client Secret into `GOOGLE_CLIENT_ID` /
   `GOOGLE_CLIENT_SECRET` in `.env` (locally) and into the Render
   dashboard's env vars (production — `render.yaml` marks these
   `sync: false` so Render prompts for them rather than reading from git).
4. Generate an encryption key for stored API keys and put it in
   `APP_ENCRYPTION_KEY` (again: `.env` locally, Render dashboard in prod):
   ```
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Losing this key makes every already-stored user API key permanently
   undecryptable — it's not something to regenerate casually once real
   users have saved keys.

Without Google credentials configured, the app still runs fine — sign-in
just won't work, and everyone gets the offline word bank.

## Run

```
python app.py
```

Then open http://127.0.0.1:5000

## Project structure

- `app.py` — `create_app()` factory; registers each game's blueprint
- `games/wordlists.py` — turns a theme into a word list (LLM or offline bank)
- `games/offline_words.py` — curated word banks + generic fallback
- `games/word_search/` — the word search game: `generator.py` (grid
  placement, pure Python, no deps), `pdf_export.py` (reportlab), and
  `routes.py` (the `/`, `/generate`, `/download/<id>.pdf` blueprint)
- `games/word_scramble/` — the word scramble game, same shape as
  `word_search/`, mounted under `/word-scramble`
- `games/sudoku/` — the sudoku game: `generator.py` (randomized
  backtracking fill + uniqueness-checked cell removal, pure Python, no
  deps), `pdf_export.py`, and `routes.py` (mounted under `/sudoku`).
  No theme or word list involved — `difficulty` is the only input.
- `config.py`, `extensions.py`, `models.py` — Flask config, SQLAlchemy/Migrate/
  Flask-Login/Authlib instances, and the `User`/`ApiKey`/`Puzzle` models
- `crypto.py` — Fernet encrypt/decrypt for stored per-user API keys
- `auth/` — Google OAuth login/callback/logout (`/auth/...`)
- `account/` — view/save/remove your own API key (`/account`)
- `migrations/` — Alembic migration scripts (`flask db migrate` / `upgrade`)
- `templates/base.html` — shared layout + nav (login state); per-game and
  per-feature templates extend it
- `static/` — shared frontend assets

More game types (crossword) will each get their own `games/<type>/`
package and blueprint alongside `word_search/`, `word_scramble/`, and
`sudoku/`.

Database: defaults to a local `instance/puzzles.db` SQLite file if
`DATABASE_URL` isn't set. In production it points at a Supabase Postgres
project (see `.env.example` for the connection-string gotchas).

## Deploy (Render)

This repo includes a `render.yaml` blueprint targeting Render's free web
service tier:

1. Push this repo to GitHub (already done if you're reading this from
   `rspahn-dev/puzzle-forge`).
2. In the [Render dashboard](https://dashboard.render.com), choose
   **New → Blueprint** and select the `puzzle-forge` repo.
3. Render prompts you for the secrets it doesn't get from git:
   `ANTHROPIC_API_KEY` (optional — offline bank works without it),
   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (needed for sign-in to
   work — see Google sign-in setup above), `APP_ENCRYPTION_KEY`
   (needed before any user can save an API key), and `DATABASE_URL`
   (a Supabase Postgres **session pooler** connection string — see
   `.env.example`; Supabase's direct connection is IPv6-only and won't
   reach Render's free IPv4 tier).
5. Deploy. Render builds with
   `pip install -r requirements.txt && flask db upgrade` (applying any
   pending migrations) and runs
   `gunicorn wsgi:app --workers 1 --bind 0.0.0.0:$PORT`.
6. Visit the assigned `*.onrender.com` URL.

Notes:
- Free tier spins down after ~15 min idle; the next request takes ~30s to
  wake it back up. Fine for low-traffic use; upgrade to a paid plan later
  for always-on if needed.
- `--workers 1` is a deliberate choice for now — future phases (auth,
  session-heavy features) haven't been load-tested beyond a single
  worker yet.

## Notes / next steps

- No rate limiting yet on `/generate` — no longer a cost concern (each
  user spends their own key's budget), but still worth adding as a
  compute/abuse guard before this is public.
- KDP/Etsy book angle: PDF export is per-puzzle today; a batch mode that
  generates N puzzles across a theme list into one bound PDF would be the
  next step for turning this into a sellable puzzle book.
