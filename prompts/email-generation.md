# email-generation.md — v4.0 (Production Design System)

## Purpose
Generate a complete, production-faithful Figma marketing email from a structured brief. Output matches real sends in `figma-examples/` — table-based HTML, no MJML, no compilation step.

## Output Format
Return a JSON object with **copy slots only** — do NOT include `html_body`. Python assembles the HTML from these fields using the v4.0 section library.

```json
{
  "subject_line": "...",
  "preview_text": "...",
  "plain_text": "...",
  "template_used": "product_launch",
  "confidence_score": 4,
  "content": {
    "headline": "...",
    "intro": "...",
    "rows": [
      {
        "title": "...",
        "body": "...",
        "link_text": "Learn more",
        "link_url": "https://figma.com/...",
        "image_alt": "..."
      }
    ],
    "bullets": [
      {"lead": "Get started:", "link_text": "Learn how", "link_url": "https://..."}
    ],
    "closing": "That's all for now :)",
    "grid": {
      "left": {"title": "...", "body": "...", "link_url": "https://..."},
      "right": {"title": "...", "body": "...", "link_url": "https://..."}
    },
    "icon_section": {"title": "And a whole lot more", "body": "..."}
  }
}
```

**Required fields by template:**

| template_type | content fields |
|---------------|----------------|
| product_launch, event_invite, reengagement | headline, intro, rows (3 items) |
| educational | headline, intro, bullets (3 items), closing |
| feature_update | headline, intro, grid.left, grid.right, icon_section |

Do NOT output HTML, MJML, or markdown fences. JSON only.

---

## Lineage Router

Pick ONE lineage based on `template_type`:

| template_type | Lineage | Font | Reference file |
|---------------|---------|------|----------------|
| product_launch | Whyte | `'Whyte', Helvetica, Arial, sans-serif` | Untitled-1 |
| event_invite | Whyte | Whyte | Untitled-1 variant |
| reengagement | Whyte | Whyte | Untitled-3 |
| educational | Whyte | Whyte | Untitled-4 |
| feature_update | Inter | `Inter, Helvetica, Arial, sans-serif` | Untitled-2 |

---

## Document Skeleton

Every email follows this structure:

```
1. <!DOCTYPE html> + <html lang="en">
2. <head> — charset, viewport, color-scheme dark, @font-face, responsive + dark mode CSS
3. Hidden preview-text div (with zero-width spacers)
4. Outer table (100% width, white background)
5. Logo wordmark (110px, figma.com link, light/dark swap)
6. [optional] Full-width hero image (640px)
7. Content sections (see template routing in email-templates.md)
8. Production footer (brand blurb + social + address + unsubscribe)
```

**Do NOT include:** view-in-browser link, email preferences link, 40px Customer.io logo.

---

## Typography

### Whyte lifecycle
| Element | Size | Weight | Padding |
|---------|------|--------|---------|
| Headline | 26px | bold | 60px sides, centered |
| Body | 20px / 28px lh | normal | 60px sides |
| Row title | 22px | bold | left-aligned |
| Row body | 18px / 22px lh | normal | left-aligned |
| Footer blurb | 14px | normal | centered, `#a5a5a5` |
| Footer legal | 12px | normal | `#B2B2B2` |

### Inter newsletter
| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| H1 | 32px | 600 | -0.5px letter-spacing |
| H2 | 22px | 600 | Section titles |
| Body | 16px / 22px lh | 400 | 0.1px letter-spacing |

---

## Color System

| Role | Hex | Where |
|------|-----|-------|
| Purple CTA + inline links | `#5551FF` | Lifecycle primary buttons, "Learn more →" |
| Black | `#000000` | Text, outline CTA border, newsletter CTA fill |
| White | `#FFFFFF` | Backgrounds |
| Resource links | `#699BF7` | Bulleted educational links |
| Footer muted | `#a5a5a5`, `#B2B2B2` | Blurb, legal, unsubscribe |

**Never use `#0D99FF` for email CTAs** — production uses `#5551FF` (lifecycle) or `#000000` (newsletter).

---

## CTA Patterns

**Purple fill** (lifecycle primary):
```html
<td style="background-color:#5551FF;border:5px solid #5551FF;border-radius:8px;font-family:'Whyte',Helvetica,Arial,sans-serif;font-size:20px;font-weight:bold;">
  <a href="[URL]" style="padding:12px 27px;color:#ffffff;text-decoration:none;display:block;">Create a file</a>
</td>
```

**Black outline** (secondary/closing):
```html
<td style="background-color:#ffffff;border:5px solid #000000;border-radius:8px;font-family:'Whyte',Helvetica,Arial,sans-serif;font-size:20px;font-weight:bold;">
  <a href="[URL]" style="padding:12px 27px;color:#000000;text-decoration:none;display:block;">Go to Figma</a>
</td>
```

**Black fill** (newsletter):
```html
<td class="btn primary" style="background:#000000;border-radius:8px;">
  <a href="[URL]" style="padding:13px 30px;color:#FFFFFF;font-family:Inter,Helvetica,Arial,sans-serif;font-size:18px;display:block;">Register now →</a>
</td>
```

Arrow links in rows: `<a style="color:#5551FF;font-weight:bold;text-decoration:none;">View the course →</a>`

---

## Section Patterns

Use the section library in `email-templates.md`. Key blocks:

1. **Image-left row** — 150px image + title/body/link (Whyte, ×3–4)
2. **Bulleted resources** — linked lead-ins at `#699BF7` (educational)
3. **Newsletter card** — 24px radius white shell (Inter)
4. **Two-column grid** — 289px columns (Inter)
5. **Icon list** — 80px icon + text (Inter)

---

## Footer (required)

410px inner table:
- Brand sentence: "Figma is a design platform for teams who build products together..."
- 5 social icons (30px): Figma, Twitter, Instagram, YouTube, LinkedIn
- Address: `Figma, Inc. · 760 Market St · San Francisco, CA 94102`
- Unsubscribe: `<a href="*|UNSUBSCRIBE|*">Unsubscribe</a>`

Use hosted icons from `static.figma.com/uploads/`.

---

## HTML Engineering Rules

1. Max width **640px** with **40px horizontal padding** on all content sections (not 600px, not edge-to-edge icons)
2. All layout tables: `role="presentation"`
3. Inline styles on every element (head CSS is supplementary)
4. Dark mode: `color-scheme` meta + `.light-img`/`.dark-img` classes
5. Preview text: hidden div with `\u00a0` spacers after text
6. Logo: 110px wordmark from `static.figma.com`, NOT Customer.io CDN
7. Return copy slots in JSON — Python builds the HTML document

---

## Quality Checklist

- [ ] Correct lineage (Whyte vs Inter) for template_type
- [ ] 640px container with 40px side padding, logo wordmark at top
- [ ] Hidden preview-text div present
- [ ] CTA uses `#5551FF` (lifecycle) or `#000000` (newsletter) — NOT `#0D99FF`
- [ ] Production footer with social icons + unsubscribe
- [ ] All images have `alt` attributes
- [ ] All layout tables have `role="presentation"`
- [ ] Subject line under 50 characters
- [ ] Preview text under 90 characters, complements subject
- [ ] No forbidden phrases (see brand guidelines)
- [ ] Arrow CTAs where appropriate ("Learn more →")

---

## Subject Line Rules
- Under 50 characters. No all-caps. Max 1 emoji.
- Warm lifecycle tone OK: "Welcome to Figma!", "A lot's happened since your last visit"

## Preview Text Rules
- Under 90 characters. Complements subject — don't repeat it.
- Matches hidden preview div content.

## Plain Text Rules
- Clean readable version. Links written out in full. Include unsubscribe.

## Confidence Score
5 = matches production patterns in figma-examples/, all checklist items pass.
1 = unsure. Be honest.

## Version History
- v4.1: LLM outputs copy slots only; Python assembles HTML via email_html.py (fixes token truncation in production).
- v4.0: Production design system from figma-examples/ — Whyte/Inter lineages, 640px, #5551FF CTAs, section library, production footer.
- v3.1: Switched from MJML to direct HTML output.
- v3.0: Abstract design system (superseded by v4.0).
