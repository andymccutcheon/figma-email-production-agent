# Handoff — Session 2026-07-20 (Interview Prep)

## What was accomplished

### Email Production Agent prototype
- **Cached demo for instant load**: Pre-generated result for "Figma AI Launch" sample
  served via `/api/cached-demo`. Pre-loaded on page load for zero-latency first click.
  "Regenerate with AI →" link shows the real LLM path on demand.
- **Asset pool (`asset_pool.py`)**: ~20 rotating Figma images with hourly deterministic
  seed so different campaigns get different visuals.
- **Customer.io sync (`sync.py`)**: Direct REST API to Design Studio using
  `CUSTOMERIO_APP_API_KEY`. Sync errors suppressed in UI since it's experimental.
- **Mobile preview fix**: Device toggle now correctly narrows iframe to 375px
  (ID selector specificity issue, fixed with `!important`).
- **Stray brace bug fix**: Extra `}` in `showResults()` was breaking the entire
  form JS. Removed.

### Presentation deck
- Fully personalized first-person, casual-tone presentation (10 slides)
- Enhanced with granular details: 5 prioritization dimension definitions,
  16 brand rule sources, pipeline module file references
- Hosted at `figma-email-production-agent.vercel.app/deck` and
  `amccutcheon.com/figma-deck` (iframe embed in portfolio)
- **TALKING-POINTS.md**: Companion speaker notes with Q&A, key numbers,
  and the full brand evaluation criteria breakdown
- Source relocated from Downloads to `docs/presentation/` in the repo

### Portfolio (`andy-portfolio` repo)
- Added `/figma-deck` route → iframe embeds the deck at `amccutcheon.com/figma-deck`

## Current state
- All 13 pipeline tests pass
- Deck CSS/JS/HTML all return 200 on production
- Customer.io sync is wired but the App API key still doesn't have
  Design Studio access — it will work once the right key type is configured
- DeepSeek fallback chain: Pro → Flash → Claude → Demo. Claude fallback
  may or may not work depending on API key configuration.

## What remains incomplete
- Customer.io sync: needs an App API key with Design Studio permissions
  (the current `a8c...` key may not have access to the design_studio scope)
- Visual regression testing (Litmus/Email on Acid) — mentioned as "left for later"
- A/B subject line flow — prompt built, not wired into the frontend
- Feedback loop for human annotations — architecture ready, not built

## Presentation deck build process
```bash
cd docs/presentation
# Set base to /static/deck/ for Flask deployment:
# vite.config.ts → base: '/static/deck/'
npm run build
# Copy to Flask static:
rm -rf ../../web/static/deck && cp -r dist ../../web/static/deck
# REVERT base back to '/' for dev:
# vite.config.ts → base: '/'
```

## Key decisions
- Brand evaluation explanation: 4 sources (guidelines, voice/tone, production analysis,
  accessibility) — not "I just used the guidelines"
- Closing slide: "That's the work." (not "That's what I built.")
- Cached demo for speed: pre-load on page load, 650ms animation, instant result
- Sync failures suppressed in UI (experimental feature, don't want red errors in demo)
