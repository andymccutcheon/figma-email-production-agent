---
name: figma-email-production
description: Generate or review Figma marketing HTML emails using the v4.0 production design system from figma-examples/.
---

# Figma Email Production Skill

Use when generating, reviewing, or debugging Figma marketing HTML emails in this POC or related projects.

---

## Project location

```
figma-me/email-production-poc/
├── figma-examples/          ← CANONICAL reference (Untitled-1 through Untitled-4)
├── email_html.py            ← v4.0 HTML building blocks (Python)
├── generate.py              ← LLM pipeline + demo templates
├── brand_check.py           ← Deterministic validation
├── context/
│   ├── email-templates.md   ← Section library + template routing
│   └── brand-guidelines.md  ← Colors, fonts, required elements
└── prompts/
    └── email-generation.md  ← LLM system prompt (v4.0)
```

---

## Before generating

1. Read the brief (`intake.py` / `EmailBrief` fields)
2. Pick lineage from `template_type`:
   - **Whyte** → product_launch, event_invite, reengagement, educational
   - **Inter** → feature_update
3. Read `context/email-templates.md` for section patterns
4. Match the closest `figma-examples/Untitled-N.html` archetype

---

## Design rules (v4.0)

| Rule | Value |
|------|-------|
| Container width | **650px** (not 600px) |
| Lifecycle font | `'Whyte', Helvetica, Arial, sans-serif` |
| Newsletter font | `Inter, Helvetica, Arial, sans-serif` |
| Primary CTA | `#5551FF` purple fill (lifecycle) or `#000000` fill (newsletter) |
| Secondary CTA | White fill, 5px black border |
| Logo | 110px wordmark from `static.figma.com` |
| Output | Complete HTML document — **no MJML** |

**Never include:** view-in-browser strip, Customer.io logo URL, `#0D99FF` CTAs.

---

## Section patterns

From `figma-examples/`:

1. Logo + hero image (650px)
2. Headline + intro body (60px side padding)
3. Purple or outline CTA button
4. Image-left rows (150px img + title/body/link) — Whyte lifecycle
5. Bulleted resource links — educational (Untitled-4)
6. Newsletter card + 2-column grid + icon list — Inter (Untitled-2)
7. Production footer (brand blurb + 5 social + address + unsubscribe)

---

## Workflow

### Generate from brief
```bash
cd figma-me/email-production-poc
python -c "from intake import EmailBrief; from generate import generate_email; ..."
```

Or use the web UI at `/` (demo mode when no API key).

### Validate output
```bash
python tests/test_pipeline.py
```

Run `BrandChecker` on generated HTML before shipping.

### Deploy
Repo: `github.com/andymccutcheon/figma-email-production-agent`
Vercel auto-deploys on push to `main`.

---

## Reference map

| File | Campaign type | Key patterns |
|------|---------------|--------------|
| Untitled-1 | Onboarding Day 0 | Whyte, purple CTA, 4× image rows |
| Untitled-2 | Release Notes newsletter | Inter, card shell, 2-col grid, icon list |
| Untitled-3 | Educational drip | Whyte, outline CTA, image rows |
| Untitled-4 | Welcome + resources | Whyte, bulleted links, outline CTA |

When in doubt, open the matching example and copy its structure — don't invent new patterns.
