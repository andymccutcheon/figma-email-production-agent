# email-generation.md — v3.1 (Design System + HTML)

## Purpose
Generate a complete, visually polished marketing email from a structured brief. Output is production-ready table-based HTML that renders in browser preview and email clients.

## Output Format
Return a JSON object:
```json
{
  "subject_line": "...",
  "preview_text": "...",
  "html_body": "<!DOCTYPE html><html>...</html>",
  "plain_text": "...",
  "template_used": "...",
  "confidence_score": 1-5
}
```
The `html_body` field MUST contain a complete HTML document with inline styles and table-based layout. Do NOT use MJML.

---

## Email Design System

### Typography Scale
| Element | Size | Weight | Color | Notes |
|---------|------|--------|-------|-------|
| Hero headline | 28px | 700 | #000000 | One per email. The main message. |
| Section heading | 20px | 600 | #000000 | Labels a content section. |
| Sub-heading | 16px | 600 | #000000 | Labels a feature or smaller block. |
| Body text | 16px | 400 | #1E1E1E | line-height: 1.6. Primary reading text. |
| Caption / footer | 12px | 400 | #666666 | Legal, unsubscribe, address. line-height: 1.5. |

**Rule:** Maximum 3 font sizes per email. Hierarchy comes from weight and spacing, not size proliferation.

### Spacing System
| Context | Value | Where |
|---------|-------|-------|
| Hero section | `padding:50px 30px` | The opening section. Generous. |
| Content section | `padding:30px 30px` | Feature lists, body copy sections. |
| Tight section | `padding:20px 30px` | Footer, secondary CTAs. |
| Text block inset | `padding:0 25px` | Left/right padding on text inside sections. |
| Between paragraphs | `padding-bottom:12px` | Space between consecutive text blocks. |
| Below heading | `padding-bottom:20px` | Space after section heading before body. |
| Around button | `padding:10px 25px` | Breathing room around CTA. |

**Rule:** White space is a design element. Crowded emails look amateur. Every section gets minimum 30px vertical padding. Every text block has 25px left/right inset. Never put text flush against a section edge.

### Color System
| Role | Color | Usage |
|------|-------|-------|
| Page background | #F5F5F5 | Entire email body background. |
| Card / section bg | #FFFFFF | Content sections. |
| Alternate section | #FAFAFA | Subtle variation for alternating rows. |
| CTA button | bg #0D99FF, text #FFFFFF | Primary action only. |
| Headings | #000000 | All heading text. |
| Body text | #1E1E1E | All reading text. Near-black for readability. |
| Muted text | #666666 | Captions, footer, view-in-browser. |

**Rule:** Limited palette. No new colors. The email feels Figma: clean, modern, restrained.

### Button Design
Use an inline-styled `<a>` tag inside a centered div:
```html
<div style="text-align:center;padding:10px 25px;">
  <a href="[URL]" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;font-weight:600;border-radius:8px;padding:14px 32px;font-size:16px;text-decoration:none;font-family:'Helvetica Neue',Arial,sans-serif;">
    [Action text]
  </a>
</div>
```
- Button text: 2-4 words, action-oriented ("Try Figma AI", "Register now")
- Always centered. Always Figma blue (#0D99FF).
- At least one text block between the headline and the button.

### Section Patterns

**Hero** — opens every email:
```html
<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#FFFFFF;width:100%;max-width:600px;margin:0 auto;">
  <tr><td style="padding:50px 30px;">
    <div style="text-align:center;padding-bottom:20px;">
      <img src="LOGO_URL" alt="Figma" width="40" style="width:40px;max-width:100%;height:auto;border:0;" />
    </div>
    <div style="font-size:28px;font-weight:700;text-align:center;padding:0 25px 12px;color:#000000;font-family:'Helvetica Neue',Arial,sans-serif;">
      [One-line main message]
    </div>
    <div style="font-size:16px;text-align:center;padding:0 25px 24px;color:#1E1E1E;line-height:1.6;font-family:'Helvetica Neue',Arial,sans-serif;">
      [One to two sentences. Tight.]
    </div>
    <!-- CTA button -->
  </td></tr>
</table>
```

**Feature Section** — alternating backgrounds, 1-3 features:
```html
<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#FAFAFA;width:100%;max-width:600px;margin:0 auto;">
  <tr><td style="padding:30px 30px;">
    <div style="font-size:20px;font-weight:600;padding:0 25px 20px;color:#000000;font-family:'Helvetica Neue',Arial,sans-serif;">[Section heading]</div>
    <div style="font-size:16px;font-weight:600;padding:0 25px 6px;color:#000000;font-family:'Helvetica Neue',Arial,sans-serif;">[Feature name]</div>
    <div style="font-size:16px;color:#1E1E1E;padding:0 25px 20px;line-height:1.6;font-family:'Helvetica Neue',Arial,sans-serif;">[One sentence describing feature and benefit.]</div>
  </td></tr>
</table>
```

**Social Proof** — optional, for credibility:
```html
<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#FFFFFF;width:100%;max-width:600px;margin:0 auto;">
  <tr><td style="padding:30px 30px;">
    <div style="font-size:16px;font-style:italic;color:#666666;text-align:center;padding:0 25px;font-family:'Helvetica Neue',Arial,sans-serif;">
      "[Short quote or stat — one line]"
    </div>
  </td></tr>
</table>
```

**CTA Repeat** — always include one near the bottom:
Use the same button markup as the hero section inside a white table section with `padding:20px 30px`.

**Footer** — closes every email:
```html
<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#FFFFFF;width:100%;max-width:600px;margin:0 auto;">
  <tr><td style="padding:20px 30px;">
    <div style="font-size:12px;color:#666666;text-align:center;padding:0 25px;font-family:'Helvetica Neue',Arial,sans-serif;">
      <a href="*|UNSUBSCRIBE|*" style="color:#666666;text-decoration:none;">Unsubscribe</a> ·
      <a href="*|PREFERENCES|*" style="color:#666666;text-decoration:none;">Email Preferences</a>
    </div>
    <div style="font-size:12px;color:#666666;text-align:center;padding:0 25px;font-family:'Helvetica Neue',Arial,sans-serif;">
      Figma, Inc. 760 Market St, San Francisco, CA 94102
    </div>
  </td></tr>
</table>
```

---

## Email Structure Template

Every email follows this skeleton. Sections marked [optional] are included only if the content supports them.

```
1. View-in-browser link (thin strip, 12px gray)
2. Logo — 40px, centered
3. HERO SECTION — headline + subhead + CTA button
4. [optional] FEATURE SECTION — 1-3 features
5. [optional] SOCIAL PROOF — quote or stat
6. CTA REPEAT — same button as hero
7. FOOTER — unsubscribe + preferences + address
```

**Maximum 5 sections total** (including hero and footer). If the content only needs 3 sections, use 3. Every section must earn its place.

---

## Visual Hierarchy Rules

1. **One story per email.** Pick the ONE thing that matters.
2. **The hero headline is the most important 6-8 words in the email.**
3. **Descending importance.** Most important at the top. Each subsequent section is less critical.
4. **Button isolation.** The CTA button must be the only tappable element at its visual weight. Don't put links next to buttons.
5. **Alternating backgrounds.** White → light gray → white → light gray helps the eye navigate.
6. **Consistent inset.** All text in a section has the same left/right padding. Nothing hugs the edge.

---

## Quality Checklist

Self-review before outputting JSON:

- [ ] Exactly ONE hero headline at 28px bold
- [ ] Logo (40px, centered) at the top
- [ ] View-in-browser link and unsubscribe link present
- [ ] At least one clear CTA button (Figma blue, 14px/32px padding)
- [ ] No more than 3 font sizes in the entire email
- [ ] Every section has at least 30px vertical padding
- [ ] All text blocks have 25px left/right padding
- [ ] Nothing is #999999 on #FFFFFF (fails contrast)
- [ ] Subject line under 50 characters
- [ ] Preview text under 90 characters, complements subject
- [ ] All `<img>` tags have `alt` attributes
- [ ] Maximum 5 sections total

---

## HTML Engineering Rules

1. Return a complete `<!DOCTYPE html>` document with `<html lang="en">`.
2. Use table-based sections (`<table role="presentation">`) for layout — max-width 600px, centered.
3. All styles must be inline on elements (no external CSS files).
4. Use styled `<a>` tags for CTAs — not raw button elements.
5. Logo URL: `https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png`
6. Do NOT use MJML tags (`<mj-*>`). Output HTML only.

## Subject Line Rules
- Under 50 characters. No all-caps. Max 1 emoji.
- Action-oriented or curiosity-driven. Reflects brief's tone.

## Preview Text Rules
- Under 90 characters. Complements subject — don't repeat it.
- Gives a reason to open.

## Plain Text Rules
- Clean, readable text version. Links written out in full.

## Voice Rules (from voice_and_tone)
- Clear over clever. No forbidden phrases (see brand guidelines).
- Write like a smart colleague, not a press release.

## Confidence Score
5 = output is clean, on-brand, follows all design system rules.
1 = unsure. Be honest — low confidence is better than wrong.

## Version History
- v3.1: Switched from MJML to direct HTML output for reliable serverless deployment.
- v3.0: Full email design system — typography scale, spacing system, color palette, section patterns, visual hierarchy rules, quality checklist.
- v2.0: Switched to MJML output. Added accessibility and engineering rules.
- v1.0: Initial prompt.
