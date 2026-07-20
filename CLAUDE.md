# CLAUDE.md — Figma Email Production POC

Standalone git repo deployed to Vercel. Parent workspace copy lives at `andy-resume-toolkit/figma-me/email-production-poc/`.

## What this is

A browser-based email production agent for Figma marketing campaigns. Takes a structured brief, generates copy via DeepSeek, assembles production-faithful HTML in Python, runs brand checks, and renders a preview.

**GitHub:** https://github.com/andymccutcheon/figma-email-production-agent  
**Live:** https://figma-email-production-agent.vercel.app  
**Skill:** `/figma-email-production`

## Architecture

- **No build system** — Python Flask app on Vercel (`@vercel/python`)
- **No MJML** — table-based HTML generated directly via `email_html.py`
- **LLM returns copy slots only** — Python assembles HTML (prevents JSON truncation)
- **Tests:** `python tests/test_pipeline.py` (13 tests)

## Key files

| Path | Purpose |
|------|---------|
| `email_html.py` | v4.0 HTML builders — layout, sections, footer |
| `generate.py` | DeepSeek/Claude/demo routing + demo templates |
| `intake.py` | Brief parsing, validation, URL normalization |
| `brand_check.py` | Deterministic brand compliance |
| `web/app.py` | Flask routes + API |
| `prompts/email-generation.md` | LLM system prompt (v4.0, copy slots) |
| `context/email-templates.md` | Section library + template routing |
| `context/brand-guidelines.md` | Colors, fonts, required elements |
| `figma-examples/` | **Canonical reference** — Untitled-1 through Untitled-4 |

## Design system (v4.0)

- **640px** container, **40px** side padding
- **Whyte** (lifecycle) or **Inter** (newsletter) fonts
- **`#5551FF`** lifecycle CTAs, **`#000000`** newsletter CTAs
- Route by `template_type`: `feature_update` → Inter; all others → Whyte
- Match closest `figma-examples/Untitled-N.html` archetype

## Environment

```bash
DEEPSEEK_API_KEY=...          # Required for live generation
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
FLASK_SECRET_KEY=...          # Session auth
```

## Commands

```bash
python tests/test_pipeline.py     # Run all tests
python web/app.py                 # Local dev on :5000
git push origin main              # Deploy to Vercel
vercel logs figma-email-production-agent
```

## Current blocker

DeepSeek returns empty content intermittently in production. See `.goose/handoff.md` for debug steps. Pipeline silently falls back to demo mode when LLM fails.

## Handoff

Session continuity: `.goose/handoff.md`
