# Session Handoff — Figma Email Production POC

**Date:** 2026-07-19  
**Repo:** https://github.com/andymccutcheon/figma-email-production-agent  
**Live:** https://figma-email-production-agent.vercel.app  
**Latest commit:** `88861a9` — fix: stack prompt template dropdown and normalize bare CTA URLs

---

## What was accomplished this session

### Pipeline fixes (production blockers resolved)

1. **Dropped MJML entirely** (`0b74262`) — Vercel Python runtime has no Node; Python MJML fallback broke on HTML entities. Now generates table-based HTML directly.
2. **v4.0 production design system** (`7e87803`) — Rebuilt from `figma-examples/` (Untitled-1 through Untitled-4). New `email_html.py` module. Whyte/Inter lineages, `#5551FF` CTAs, production footer.
3. **Fixed LLM JSON truncation** (`51fde15`) — DeepSeek was embedding full HTML in JSON and hitting token limits. LLM now returns copy slots only; Python assembles HTML.
4. **Layout polish** (`4d06b85`) — 640px container, 40px side padding on all content sections via `content_section()` wrapper.
5. **UI + validation** (`88861a9`) — Prompt template dropdown stacked under header; bare CTA domains auto-normalize to `https://`.

### Skills & docs

- `/figma-email-production` skill added to POC repo and `andy-resume-toolkit/.claude/skills/`
- All 4 production reference emails committed to `figma-examples/`
- 13 tests passing locally (`python tests/test_pipeline.py`)

---

## Known blockers (next session priority)

### 1. DeepSeek empty content (CURRENT)

**Symptom:** `[generate] DeepSeek failed: DeepSeek returned empty content — the model may not support this request or the prompt was rejected`

**Location:** `generate.py` → `_call_deepseek()` line ~336

**Likely causes:**
- V4 thinking mode defaults to **enabled** — reasoning tokens land in `reasoning_content`, leaving `content` empty for JSON tasks (fixed in next deploy: `thinking: disabled`)
- System prompt + context files may exceed model limits or trigger content filter
- API returns `choices[0].message.content` as empty string with no error HTTP code

**Recommended fixes (in order):**
1. Log full API response body when content is empty (include `finish_reason`, `usage`, model name)
2. Verify model names against DeepSeek docs — try `deepseek-chat` / `deepseek-reasoner` as env overrides
3. Add retry with truncated system prompt (strip `figma-examples` references from prompt, keep `email-templates.md` summary)
4. Track **actual** provider used per request — `get_active_provider()` returns "DeepSeek" whenever key is set, even after silent fallback to demo (misleading UI)

### 2. Silent fallback to demo mode

When DeepSeek fails, pipeline falls through to `_generate_demo()` without surfacing the error to the UI. User sees an email but copy is generic demo content, not LLM-generated.

**Fix:** Return `provider: "demo-fallback"` + `generation_warning` in API response when LLM fails.

---

## Architecture (current)

```
Brief (intake.py)
  → validate + normalize URLs
  → generate.py
      → DeepSeek: copy slots JSON (~1KB)
      → email_html.py: assemble HTML (~10KB)
      → brand_check.py
      → preview.py
  → web/app.py (Flask on Vercel)
```

**Key files:**

| File | Role |
|------|------|
| `email_html.py` | v4.0 HTML builders — single source of layout truth |
| `generate.py` | LLM calls + demo templates + HTML assembly |
| `prompts/email-generation.md` | v4.0 — copy slots only, no html_body |
| `context/email-templates.md` | Section library + template routing |
| `figma-examples/` | Canonical production reference emails |
| `brand_check.py` | Deterministic validation (Whyte/Inter, #5551FF, 640px) |

**Env vars (Vercel):**
- `DEEPSEEK_API_KEY` — required for live generation (one key works for all models)
- `DEEPSEEK_PRO_MODEL` — optional model ID override, default `deepseek-v4-pro`
- `DEEPSEEK_FLASH_MODEL` — optional model ID override, default `deepseek-v4-flash`
- `FLASK_SECRET_KEY` — session auth

---

## Design tokens (v4.0 / v4.1)

| Token | Value |
|-------|-------|
| Container | 640px max-width |
| Side padding | 40px (`SIDE_PADDING` in `email_html.py`) |
| Lifecycle font | Whyte |
| Newsletter font | Inter |
| Lifecycle CTA | `#5551FF` purple fill |
| Newsletter CTA | `#000000` black fill |
| Secondary CTA | White + 5px black border |
| Output | HTML only — no MJML, no compilation |

---

## Recommended next steps

1. **Debug DeepSeek empty content** — add response logging, verify model IDs, test with minimal prompt locally
2. **Fix provider reporting** — track actual provider per generation, show warning on fallback
3. **Vercel log check** after fix — `vercel logs figma-email-production-agent --follow`
4. **Visual QA** — regenerate each of 5 template types on live site; compare against `figma-examples/`
5. **Optional:** Add Claude as primary if DeepSeek model IDs remain unstable

---

## Key decisions & rationale

| Decision | Rationale |
|----------|-----------|
| Drop MJML | Vercel Python has no Node at runtime; compilation always failed in prod |
| Copy slots + Python assembly | Prevents JSON truncation; deterministic HTML matches demo path |
| `figma-examples/` as source of truth | Real production sends, not abstract design rules |
| 640px / 40px padding | User feedback — icons were flush against left edge at 650px |
| Normalize bare URLs | Prompt templates use `help.figma.com/...` without scheme |
| No view-in-browser strip | Production Figma emails don't include it |

---

## Commands

```bash
cd figma-me/email-production-poc

# Run tests
python tests/test_pipeline.py

# Local dev (needs .env with DEEPSEEK_API_KEY)
python web/app.py

# Deploy
git push origin main   # Vercel auto-builds

# Logs
vercel logs figma-email-production-agent
```
