# email-generation.md — v3.0 (Design System + MJML)

## Purpose
Generate a complete, visually polished marketing email from a structured brief. Output is valid MJML XML that compiles to cross-client HTML.

## Output Format
Return a JSON object:
```json
{
  "subject_line": "...",
  "preview_text": "...",
  "html_body": "<mjml>...</mjml>",
  "plain_text": "...",
  "template_used": "...",
  "confidence_score": 1-5
}
```
The `html_body` field MUST contain valid MJML XML. It will be compiled to HTML automatically.

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
| Hero section | `padding="50px 30px"` | The opening section. Generous. |
| Content section | `padding="30px 30px"` | Feature lists, body copy sections. |
| Tight section | `padding="20px 30px"` | Footer, secondary CTAs. |
| Text block inset | `padding="0 25px"` | Left/right padding on text inside columns. |
| Between paragraphs | `padding-bottom="12px"` | Space between consecutive text blocks. |
| Below heading | `padding-bottom="20px"` | Space after section heading before body. |
| Around button | `padding="10px 25px"` | Breathing room around CTA. |

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
```xml
<mj-button href="[URL]" background-color="#0D99FF" color="#FFFFFF"
  font-weight="600" border-radius="8px" padding="14px 32px"
  font-size="16px" align="center">
  [Action text]
</mj-button>
```
- Button text: 2-4 words, action-oriented ("Try Figma AI", "Register now")
- Always centered. Always Figma blue (#0D99FF).
- At least one text block between the headline and the button.

### Section Patterns

**Hero** — opens every email:
```xml
<mj-section background-color="#FFFFFF" padding="50px 30px">
  <mj-column>
    <mj-image src="LOGO_URL" alt="Figma" width="40px" align="center" padding-bottom="20px" />
    <mj-text font-size="28px" font-weight="700" align="center" padding="0 25px" padding-bottom="12px">
      [One-line main message]
    </mj-text>
    <mj-text font-size="16px" align="center" padding="0 25px" padding-bottom="24px" color="#1E1E1E">
      [One to two sentences. Tight.]
    </mj-text>
    <mj-button href="[URL]">[CTA]</mj-button>
  </mj-column>
</mj-section>
```

**Feature Section** — alternating backgrounds, 1-3 features:
```xml
<mj-section background-color="#FAFAFA" padding="30px 30px">
  <mj-column>
    <mj-text font-size="20px" font-weight="600" padding="0 25px" padding-bottom="20px">
      [Section heading]
    </mj-text>
    <mj-text font-size="16px" font-weight="600" padding="0 25px" padding-bottom="6px">
      [Feature name]
    </mj-text>
    <mj-text font-size="16px" color="#1E1E1E" padding="0 25px" padding-bottom="20px">
      [One sentence describing feature and benefit.]
    </mj-text>
    <!-- Repeat for additional features -->
  </mj-column>
</mj-section>
```

**Social Proof** — optional, for credibility:
```xml
<mj-section background-color="#FFFFFF" padding="30px 30px">
  <mj-column>
    <mj-text font-size="16px" font-style="italic" color="#666666" align="center" padding="0 25px">
      "[Short quote or stat — one line]"
    </mj-text>
  </mj-column>
</mj-section>
```

**CTA Repeat** — always include one near the bottom:
```xml
<mj-section background-color="#FFFFFF" padding="20px 30px">
  <mj-column>
    <mj-button href="[URL]">[Same CTA as hero]</mj-button>
  </mj-column>
</mj-section>
```

**Footer** — closes every email:
```xml
<mj-section background-color="#FFFFFF" padding="20px 30px">
  <mj-column>
    <mj-text font-size="12px" color="#666666" align="center" padding="0 25px">
      <a href="*|UNSUBSCRIBE|*" style="color:#666666;">Unsubscribe</a> &middot;
      <a href="*|PREFERENCES|*" style="color:#666666;">Email Preferences</a>
    </mj-text>
    <mj-text font-size="12px" color="#666666" align="center" padding="0 25px">
      Figma, Inc. 760 Market St, San Francisco, CA 94102
    </mj-text>
  </mj-column>
</mj-section>
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
- [ ] All `<mj-image>` have `alt` attributes
- [ ] Maximum 5 sections total

---

## MJML Engineering Rules

1. All visible content in `<mj-column>` inside `<mj-section>`.
2. Root element: `<mjml lang="en">`.
3. Use `<mj-title>` for the email title.
4. Never nest `<mj-section>` inside another `<mj-section>`.
5. Use `<mj-button>` for CTAs — never raw `<a>` tags for buttons.
6. Logo URL: `https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png`

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
- v3.0: Full email design system — typography scale, spacing system, color palette, section patterns, visual hierarchy rules, quality checklist.
- v2.0: Switched to MJML output. Added accessibility and engineering rules.
- v1.0: Initial prompt.
