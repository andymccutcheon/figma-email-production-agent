# Figma Email Production Agent

Generate production-faithful Figma marketing HTML emails from structured briefs. LLM writes copy; Python assembles table-based HTML matching real sends in `figma-examples/`.

**Live demo:** https://figma-email-production-agent.vercel.app  
**Repo:** https://github.com/andymccutcheon/figma-email-production-agent

---

## Quick start

```bash
# Clone
git clone https://github.com/andymccutcheon/figma-email-production-agent.git
cd figma-email-production-agent

# Env
cp .env.example .env   # add DEEPSEEK_API_KEY

# Test
python tests/test_pipeline.py

# Local dev
python web/app.py      # http://localhost:5000
```

Deploy: push to `main` → Vercel auto-builds.

---

## How it works

```
Brief → intake.py (validate)
      → generate.py (DeepSeek copy slots OR demo templates)
      → email_html.py (assemble HTML)
      → brand_check.py
      → preview
```

- **No MJML** — HTML is built directly (Vercel Python has no Node)
- **Copy slots pattern** — LLM returns ~1KB JSON; Python builds ~10KB HTML (avoids token truncation)
- **v4.0 design system** — derived from 4 real Figma production emails in `figma-examples/`

---

## Repo structure

```
├── email_html.py           # v4.0 HTML builders (layout source of truth)
├── generate.py             # LLM routing + demo templates
├── intake.py               # Brief parsing + URL normalization
├── brand_check.py          # Brand compliance validation
├── preview.py              # HTML preview renderer
├── figma-examples/         # Canonical production reference emails
├── context/
│   ├── email-templates.md  # Section library + routing
│   ├── brand-guidelines.md
│   └── voice-and-tone.md
├── prompts/
│   ├── email-generation.md # v4.0 LLM prompt (copy slots)
│   ├── brand-compliance.md
│   └── subject-line.md
├── tests/test_pipeline.py  # 13 automated tests
├── web/                    # Flask app (Vercel entry point)
│   ├── app.py
│   ├── static/
│   └── templates/
├── docs/                   # Study guide, test prompts
├── ARCHITECTURE.md         # System design
├── CLAUDE.md               # Agent instructions
└── .goose/handoff.md       # Session handoff notes
```

---

## Design tokens

| Token | Value |
|-------|-------|
| Container | 640px |
| Side padding | 40px |
| Lifecycle font | Whyte |
| Newsletter font | Inter |
| Lifecycle CTA | `#5551FF` |
| Newsletter CTA | `#000000` |

Template routing: `feature_update` → Inter newsletter; everything else → Whyte lifecycle.

---

## Template archetypes

| template_type | Reference | Patterns |
|---------------|-----------|----------|
| product_launch | Untitled-1 | Purple CTA, 3× image-left rows |
| event_invite | Untitled-1 variant | Same lifecycle layout |
| feature_update | Untitled-2 | Inter card, 2-col grid, icon list |
| reengagement | Untitled-3 | Outline CTA, image rows |
| educational | Untitled-4 | Bulleted links, outline CTA |

---

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `DEEPSEEK_API_KEY` | For live mode | — (one key works for all models) |
| `DEEPSEEK_PRO_MODEL` | No | `deepseek-v4-pro` (model ID, not a separate key) |
| `DEEPSEEK_FLASH_MODEL` | No | `deepseek-v4-flash` (model ID, not a separate key) |
| `FLASK_SECRET_KEY` | Prod | auto-generated |
| `ANTHROPIC_API_KEY` | No | Claude fallback |

---

## Known issues

See `.goose/handoff.md` for current blockers. As of 2026-07-19:

- DeepSeek may return empty content in production → silent fallback to demo mode
- UI shows "DeepSeek" even when demo fallback was used

---

## Agent skill

Use `/figma-email-production` in Claude Code. Skill lives in `.claude/skills/figma-email-production/SKILL.md`.
