# Figma Brand Guidelines

> Derived from Figma's public brand assets and design language.
> These rules are enforced deterministically in the brand checker — not left to LLM judgment.

## Logo

- The Figma logo is a 5-color shape (blue, green, orange, red, purple)
- Must appear at the top of every email
- Link: figma.com
- Alt text: "Figma"
- The wordmark is "Figma" in black, set in a custom sans-serif typeface
- Asset: `https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png` (5-color mark, hosted on Customer.io CDN for reliable email display)

## Primary Color Palette

| Color | Hex | Usage |
|———-|——-|———-|
| Black | `#000000` | Headlines, body text, wordmark |
| Near Black | `#1E1E1E` | Secondary text |
| Figma Blue | `#0D99FF` | Primary CTA, links |
| Figma Purple | `#9747FF` | Accent, hover states |
| White | `#FFFFFF` | Backgrounds, text on dark |
| Light Gray | `#F5F5F5` | Section backgrounds |

## Extended Palette (Figma brand colors)

These are the canonical Figma brand colors used in the logo and product.  
Use sparingly in marketing — reserve for visual accents, not body text or CTAs.

| Color | Hex |
|———-|——-|
| Logo Blue | `#00B6FF` |
| Logo Green | `#24CB71` |
| Logo Orange | `#FF7237` |
| Logo Red | `#FF3737` |
| Logo Purple | `#874FFF` |

## UI Tint Palette

Used for icon backgrounds, badges, section accents:

| Tint | Hex |
|———|——-|
| Blue tint | `#E5F4FF` |
| Green tint | `#CFF7D3` |
| Purple tint | `#F1E5FF` |
| Orange tint | `#FFDFCC` |
| Pink tint | `#FFE0FC` |
| Indigo tint | `#EBEBFF` |
| Gray tint | `#E3ECF2` |

## Typography

Production emails use two typefaces — never Helvetica Neue:

| Lineage | Font Stack | Used for |
|---------|------------|----------|
| **Whyte** (lifecycle) | `'Whyte', Helvetica, Arial, sans-serif` | Onboarding, product launch, re-engagement, educational |
| **Inter** (newsletter) | `Inter, Helvetica, Arial, sans-serif` | Feature updates, release notes |

### Whyte scale

| Element | Size | Weight |
|---------|------|--------|
| Headline | 26px | bold |
| Body | 20px | normal |
| Row title | 22px | bold |
| Row body | 18px | normal |
| Footer blurb | 14px | normal |
| Footer legal | 12px | normal |

### Inter scale

| Element | Size | Weight |
|---------|------|--------|
| H1 | 32px | 600 |
| H2 | 22px | 600 |
| Body | 16px | 400 |

## CTAs (v4.0 production)

| Style | Background | Border | Text | When |
|-------|------------|--------|------|------|
| Purple fill | `#5551FF` | 5px `#5551FF` | white | Lifecycle primary (onboarding, launch) |
| Black outline | white | 5px `#000000` | black | Secondary / closing (re-engagement) |
| Black fill | `#000000` | 3px `#000000` | white | Newsletter primary |

Inline row links: `#5551FF` bold with arrow (→). Educational resource links: `#699BF7`.

**Do not use `#0D99FF` for email CTAs** — that is product UI blue, not email production blue.

## Required Elements (Every Email)

1. Figma logo wordmark (110px, linked to figma.com) — from `static.figma.com`
2. Hidden preview-text div with spacers
3. Unsubscribe link (footer)
4. Physical address (footer): Figma, Inc. · 760 Market St · San Francisco, CA 94102
5. Alt text on all images
6. Production footer: brand blurb + 5 social icons

**Not required in production:** view-in-browser link, email preferences link.

## Forbidden

- Using the 5-color logo mark as a standalone element without proper spacing
- Red (`#FF3737`) and orange (`#FF7237`) for CTAs or positive actions
- All-caps body text
- More than 2 exclamation marks total
- "Click here" as link text
- Images without alt text
- Generic marketing language: "revolutionary", "game-changing", "disruptive", "best-in-class", "industry-leading"
