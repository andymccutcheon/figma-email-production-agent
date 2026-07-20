# Email Templates v4.0 (Production HTML)

> Canonical reference: `figma-examples/` (Untitled-1 through Untitled-4).
> Two design lineages. All output is table-based HTML with inline styles — no MJML.

## Design Lineages

| Lineage | Font | Width | Used for |
|---------|------|-------|----------|
| **Whyte** (lifecycle) | `'Whyte', Helvetica, Arial, sans-serif` | 650px | product_launch, event_invite, reengagement, educational |
| **Inter** (newsletter) | `Inter, Helvetica, Arial, sans-serif` | 650px | feature_update |

Route by `template_type`. Never mix fonts within one email.

---

## Required Elements (every template)

1. `<!DOCTYPE html>` with `lang="en"`
2. `<head>` with charset, viewport, `color-scheme: light dark`, and `@font-face`
3. Hidden preview-text div with zero-width spacers (prevents client clipping)
4. Logo wordmark (110px) linked to figma.com — light/dark swap via `.light-img` / `.dark-img`
5. Full-width hero image (650px) when the archetype uses one
6. Production footer: brand blurb + 5 social icons + address + unsubscribe
7. All `<table role="presentation">` for layout; all `<img>` have `alt`

**Do NOT include** (not in production examples): view-in-browser strip, email preferences link, Customer.io logo URL.

---

## Section Library

### 1. Logo Block (Whyte + Inter)

110px Figma wordmark, top-left padding. Light logo + hidden dark logo for dark mode.

```
Logo light: https://static.figma.com/uploads/f2c739b51898125e6ab81e67036787f570c03b0e
Logo dark:  https://static.figma.com/uploads/53280c3b3748be75104b3f237318ba3036b959b7
```

### 2. Hero Image

Full-width 650px image, linked to primary CTA URL. Alt describes the visual.

### 3. Headline + Intro (Whyte)

- Headline: 26px bold, centered, 60px horizontal padding
- Body: 20px / 28px line-height, 60px horizontal padding
- Inline links: `#5551FF` bold, no underline

### 4. CTA Buttons

| Style | When | CSS |
|-------|------|-----|
| **Purple fill** | Primary lifecycle action (onboarding, launch) | bg `#5551FF`, white text, 5px border, 8px radius |
| **Black outline** | Secondary / closing (re-engagement, educational) | white bg, 5px `#000000` border, black text |
| **Black fill** | Newsletter primary | bg `#000000`, white text, 8px radius (Inter) |

CTA text uses arrows: "Create a file", "Go to Figma", "Register now →"

### 5. Image-Left Row (Whyte lifecycle)

Used 3–4× in onboarding/product emails (Untitled-1, Untitled-3):

```
[150px image] | Title (22px bold)
              | Body (18px / 22px)
              | Link → (#5551FF bold)
```

60px right padding on text column. 50px bottom spacing between rows.

### 6. Bulleted Resource List (Whyte educational — Untitled-4)

20px body copy with linked lead-ins at `#699BF7`:

```
Get started with comments: Learn how
Explore templates: Browse the gallery
```

### 7. Newsletter Card Shell (Inter — Untitled-2)

White card with 24px border-radius wrapping hero + content. Used for feature_update / release notes.

### 8. Two-Column Grid (Inter newsletter)

289px columns side-by-side. Image + H2 (22px/600) + body (16px) + "Learn more →" link.

### 9. Icon List (Inter newsletter)

80px icon left, title + body right. For "and a whole lot more" sections.

### 10. Production Footer

410px inner table, centered:
- Brand sentence (14px, `#a5a5a5`)
- 5 social icons (30px, 30px gaps): Figma, Twitter, Instagram, YouTube, LinkedIn
- Address: `Figma, Inc. · 760 Market St · San Francisco, CA 94102` (12px, `#B2B2B2`)
- Unsubscribe link only (no preferences)

---

## Template Routing

| template_type | Archetype | Reference | Sections |
|---------------|-----------|-----------|----------|
| `product_launch` | Whyte onboarding | Untitled-1 | logo → hero → headline → intro → purple CTA → 3× image rows → purple CTA → footer |
| `event_invite` | Whyte lifecycle | Untitled-1 variant | logo → hero → headline → date+message → purple CTA → 3× image rows → purple CTA → footer |
| `feature_update` | Inter newsletter | Untitled-2 | logo → card(hero → headline → intro → 2-col grid → icon list → black CTA) → footer |
| `reengagement` | Whyte educational | Untitled-3 | logo → hero → headline → intro → 3× image rows → outline CTA → footer |
| `educational` | Whyte resources | Untitled-4 | logo → hero → headline → intro → bulleted links → sign-off → outline CTA → footer |

---

## Typography Tokens

### Whyte (lifecycle)

| Element | Size | Weight | Line-height |
|---------|------|--------|-------------|
| Headline | 26px | bold | 30px |
| Body | 20px | normal | 28px |
| Row title | 22px | bold | 28px |
| Row body | 18px | normal | 22px |
| Row link | 18px | bold | 21px |
| Footer blurb | 14px | normal | 20px |
| Footer legal | 12px | normal | 18px |

### Inter (newsletter)

| Element | Size | Weight | Line-height |
|---------|------|--------|-------------|
| H1 | 32px | 600 | 30px (-0.5px tracking) |
| H2 | 22px | 600 | 28px |
| Body | 16px | 400 | 22px (0.1px tracking) |

---

## Color Tokens

| Role | Hex | Usage |
|------|-----|-------|
| Purple CTA / inline links | `#5551FF` | Primary lifecycle CTAs, "Learn more →" links |
| Black | `#000000` | Text, outline CTA border, newsletter CTA fill |
| White | `#FFFFFF` | Backgrounds, CTA text on purple/black |
| Resource links | `#699BF7` | Bulleted educational links (Untitled-4) |
| Footer muted | `#a5a5a5` / `#B2B2B2` | Brand blurb, legal, unsubscribe |
| Border | `#DEDEDE` | Footer top rule |

**Do not use** `#0D99FF` for email CTAs — production lifecycle emails use `#5551FF`.

---

## Engineering Patterns (from production)

- Container: `max-width: 650px`, centered
- All layout tables: `role="presentation"`
- Dark mode: `color-scheme: light dark` meta + `.light-img`/`.dark-img` swap + `[data-ogsc]` for Android
- Preview text: hidden div + `\u00a0` / zero-width spacers
- Hosted assets: `static.figma.com/uploads/...`
- Inline styles duplicate `<head>` utility classes for client fallback
