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
