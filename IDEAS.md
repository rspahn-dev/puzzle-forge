# Ideas

## Scaling the offline (no-AI) word bank

Problem: `games/offline_words.py` only covers ~16 curated themes plus a
handful of keyword variants. Anything else typed as a theme falls through
to `GENERIC_BANK` — irrelevant mood/nature filler words (see the "dogs"
bug, fixed by adding a dedicated bank). This is a real risk for an
Etsy/KDP puzzle-book business built on flexible themes, since most
customer-requested themes won't be in the curated list.

Options, roughly in order of effort-to-coverage ratio:

1. **One-time LLM batch-generation, baked into static data (recommended)**
   Use the site's own `generate_word_list()` once, offline, across a
   couple hundred seed themes (dogs, cats, cars, coffee, camping,
   weddings, etc.), and save the results as a `themes.json` that
   `offline_words.py` loads instead of (or alongside) the hardcoded
   `THEME_BANKS` dict. One-time API cost (likely under $1 with Haiku)
   instead of paying per-puzzle forever. Directly fixes the
   generic-fallback bug. Needs a small generation script + a real
   (cheap) paid API call to run it — do this with explicit go-ahead
   since it spends real money, however small.

2. **WordNet-based auto-expansion**
   Bundle NLTK's WordNet corpus (free, offline, downloaded once) and
   pull related words for *any* typed theme via hypernym/hyponym trees.
   Scales to unlimited themes with zero per-theme curation and no
   ongoing cost, but relevance is noisier — WordNet gives taxonomically
   related words, not necessarily "good word-search words" — so it
   needs a filtering pass on top. More robust long-term, more
   engineering work up front.

3. **Keep manually adding curated banks**
   What was done for "dogs" — highest quality, but doesn't scale past
   however many themes you're willing to hand-write one at a time.

## Saving generated books to the account (scoped, not yet built)

Problem: `games/batch/routes.py` builds each book's PDF to a tempfile,
streams it back, then deletes it (`export_*_batch` → `send_file` →
`after_this_request` cleanup) — nothing is persisted, logged in or not.
Regenerating a book (to fix a typo in the title, tweak themes, etc.) means
literally starting over, re-spending any live-API cost. Login currently
does almost nothing besides letting a user store their own Anthropic key
(see `account/routes.py`), so this is also the most natural feature to add
to the login area.

**Schema** — new `Book` model in `models.py`, separate from the existing
`Puzzle` table (batch mode doesn't use `Puzzle` at all today):

```python
class Book(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    game_type = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(200))
    puzzle_count = db.Column(db.Integer)
    pdf_data = db.Column(db.LargeBinary, nullable=False)
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=_now)
```

`user_id` non-nullable — only save for logged-in users; storing PDFs for
anonymous requests forever is pure liability with no way to retrieve them.

**Hook point** — `games/batch/routes.py:149`, right before `send_file`: if
`current_user.is_authenticated`, read the tempfile's bytes and insert a
`Book` row before cleanup deletes the file. One extra DB write, no change
to the response the caller gets today.

**Retrieval** — two new routes, likely under `account_bp` since that's
already the "your stuff" area:
- `GET /account/books` — list titles/dates/puzzle counts, newest first
- `GET /account/books/<id>.pdf` — stream `pdf_data` back, same
  `send_file`/`download_name` pattern used elsewhere

**Size/cost** — puzzle-book PDFs are typically low hundreds of KB to a few
MB; Postgres handles that fine as `bytea` at this scale (Supabase free
tier). Not a real cost concern unless usage gets heavy.

**Guardrails worth adding**: a per-user cap (e.g. keep the last 20 books,
delete oldest on insert) so this can't grow unbounded from
regenerate-while-tweaking sessions, plus a delete action on the list page.

**Migration**: one `flask db migrate` + `flask db upgrade` for the new
table — Flask-Migrate is already set up (`migrations/`).

Scope is small: one model, one insert in an existing route, two new read
routes, one migration.

## Monetization: Etsy/KDP books vs. the site itself

Two paths were discussed. Decision: focus on the puzzle-book path first —
selling on the site directly (ads/subscriptions) needs real traffic before
it's worth setting up, and traffic doesn't exist yet. Books can generate
revenue immediately using batch mode as it already stands.

### Path A: Etsy — sell the PDF as a digital download

Fees (US seller, verify current numbers before publishing — Etsy changes
these occasionally):
- $0.20 per listing, renews every 4 months or immediately on a sale
- 6.5% transaction fee on the sale price
- ~3% + $0.25 payment processing

Rough example — a themed puzzle book (like the 27-puzzle gardening word
search sample) priced at $7.99:
- Etsy/payment fees ≈ $0.20 (listing) + $0.52 (transaction) + $0.49
  (processing) ≈ $1.21
- Net ≈ $6.78/sale, and production cost is effectively $0 since the book
  is self-generated (no printing, no inventory)

Pros: instant global listing, no print/inventory cost, fast iteration
(new theme = new listing in minutes with batch mode). Cons: the
low-content-book category is crowded — the niche-theming work (gardening
sub-themes, real crossword clues) is what's supposed to be the
differentiator, not novelty of format.

### Path B: Amazon KDP — print-on-demand paperback

Royalty structure (verify against current KDP terms before publishing):
- 60% royalty on standard (Amazon.com) distribution, minus print cost
- 40% royalty if "expanded distribution" (other retailers/libraries) is
  enabled
- Print cost for a B&W interior paperback ≈ $0.85 + $0.012 × page count
  (this formula holds up to a few hundred pages; there's a different
  rate beyond that)

Rough example — a 60-puzzle book (~130 pages with cover pages + answer
key), list price $8.99:
- Print cost ≈ $0.85 + $0.012 × 130 ≈ $2.41
- Royalty ≈ 60% × $8.99 − $2.41 ≈ $2.98/sale (standard distribution)

Pros: Amazon handles printing, shipping, and returns automatically —
zero fulfillment work; built-in massive audience/search. Cons: lower
per-unit margin than the Etsy digital path, royalties paid out on a
~60-day delay, and the paperback format takes more PDF polish (bleed,
margins, page count rules) than a digital download does.

### Path C (deprioritized): monetizing the site directly

Ideas floated: ads, a premium/subscription tier gating batch mode or
higher puzzle limits, etc. Shelved because none of it pays off without
existing traffic, and puzzle-forge doesn't have meaningful traffic yet.
Revisit once book sales are validated and/or driving traffic back to the
site — the "saving generated books to the account" feature above would
also make more sense as a real premium-tier lever at that point.
