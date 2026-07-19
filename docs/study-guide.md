# Email Production Agent — Study Guide

> Private reference for speaking to every aspect of this prototype.
> Architecture decisions, technology choices, design rationale, and tradeoffs.

---

## 1. What It Is

An AI-powered email production pipeline that takes a campaign brief (structured form or freeform text) → generates a complete, brand-compliant marketing email → renders a cross-client preview → syncs to Customer.io.

Built as a prototype for **Figma's Marketing Engineering** team. Goal: demonstrate how AI can compress the email production workflow from hours (brief → copy → design → review → build → QA → send) to minutes.

---

## 2. Pipeline Architecture

```
Brief Input → LLM Generation → MJML Compilation → Brand Check → Preview → Sync
```

### Step-by-step

| Step | What happens | Technology |
|------|-------------|------------|
| **1. Intake** | Brief collected via web UI (structured form or freeform text) | Flask, vanilla JS |
| **2. Parse** (freeform only) | Freeform text → structured brief fields via LLM | DeepSeek Flash |
| **3. Generate** | Structured brief + brand context → complete MJML email | DeepSeek Pro (OpenAI-compatible API) |
| **4. Compile** | MJML XML → production HTML with cross-client compatibility | `npx mjml` (Node.js) |
| **5. Brand Check** | Deterministic validation of compiled HTML against brand rules | Python (regex + structural analysis) |
| **6. Preview** | HTML rendered in desktop (600px) + mobile (375px) iframes | srcdoc injection |
| **7. Sync** | Push to Customer.io Design Studio for final QA | `cio` CLI / API |

### Why two LLMs?
- **DeepSeek Pro** (`deepseek-v4-pro`): Full email generation — creative, structured output requiring high-quality reasoning
- **DeepSeek Flash** (`deepseek-v4-flash`): Brief parsing + subject line variations — lighter, faster, lower-cost tasks

Using the same provider with different model tiers keeps the API surface simple while optimizing cost.

---

## 3. Why MJML (Not Raw HTML, Not React Email)

### The problem
Email HTML is notoriously difficult. Every client renders differently:
- **Outlook** uses Word's rendering engine (yes, Microsoft Word) — no flexbox, no grid, limited CSS
- **Gmail** strips `<style>` tags, clips messages at 102KB
- **Apple Mail** supports modern CSS but has dark mode quirks
- **Mobile clients** have inconsistent media query support

Hand-writing HTML that works everywhere is a specialized skill. Letting an LLM generate raw HTML would produce beautiful emails that **break in Outlook** (40%+ of enterprise email opens).

### Why MJML specifically
MJML is an open-source framework (by Mailjet/Mailgun) that abstracts email HTML into a clean XML component language. It:
- **Compiles to table-based HTML with Outlook VML conditionals** — handles the Word rendering engine automatically
- **Outputs responsive HTML** without the author writing media queries
- **Minifies output** to stay under Gmail's 102KB clip limit
- **Has 4+ years of battle-testing** across every major email client

### Why not React Email
React Email is excellent for hand-coded templates (component reuse, TypeScript safety, visual editor). But for **LLM-generated** email:
- LLMs natively output text — MJML XML is far more natural for them than TypeScript React components
- React Email still requires compilation (to HTML via `render()` or `resend` CLI), same as MJML
- MJML's component model (`<mj-section>`, `<mj-column>`, `<mj-text>`) maps more directly to email concepts than React components do
- MJML handles Outlook VML generation natively; React Email requires manual VML handling

**Decision:** MJML for generation, with the understanding that in production, teams could export to React Email for hand-tuning if needed.

---

## 4. Brand Compliance — Deterministic, Not Probabilistic

### Philosophy
Asking an LLM "is this email on-brand?" is unreliable. LLMs hallucinate, miss things, and can't be trusted for binary compliance decisions. Instead, **all brand rules are enforced in code** (`brand_check.py`).

### Brand checks (13 rules)

| Category | Rule | Severity |
|----------|------|----------|
| **Required elements** | Logo link to figma.com | Critical |
| | Unsubscribe link | Critical |
| | View-in-browser link | Warning |
| | Alt text on all images | Critical |
| **Forbidden content** | Forbidden phrases (revolutionary, game-changing, etc.) | Warning |
| | "Click here" as link text | Warning |
| | More than 2 exclamation marks | Warning |
| | All-caps body text | Warning |
| **Visual brand** | CTA color must be #0D99FF (Figma Blue) | Warning |
| | Font must be Helvetica Neue / Arial / sans-serif | Critical |
| | Red (#F24822) only in alerts | Warning |
| **Content quality** | Subject line under 50 characters | Warning |
| **Accessibility** | Heading hierarchy (single h1, no skips) | Warning |
| | Layout tables have role="presentation" | Warning |
| | Descriptive link text (not "click here") | Warning |
| | `<title>` tag present | Warning |
| | `lang` attribute on root element | Warning |

### Why deterministic
- **Reproducible:** Same input always produces the same result
- **Auditable:** Every violation has a specific rule and location
- **Fast:** No API call needed — runs in milliseconds
- **Reliable:** Can't hallucinate or miss things

---

## 5. Accessibility — Beyond "Good Enough"

The email accessibility rules come from the `email-best-practices` skill and the Email Marketing Coalition's 2026 accessibility report. Key findings from that report:

- **96% of marketing emails fail automated accessibility checks**
- Even emails that pass automation still have issues: generic alt text, heading misuse, low contrast on footers
- Screen reader users report email as the most frustrating digital experience

### What we check (and why)

| Check | Why it matters |
|-------|---------------|
| **Single `<h1>`** | Screen readers navigate by headings. Multiple h1s or no headings = disorienting. |
| **No heading skips** | Jumping from h1 → h3 confuses the document outline. |
| **Alt text on every image** | Images are blocked by default in most clients. Alt text is what people see. |
| **`alt=""` on decorative images** | Tells screen readers to skip spacers/dividers. Omitting alt entirely is worse — some readers announce the filename. |
| **Descriptive link text** | "Click here" is meaningless out of context. Screen readers often list all links on a page. |
| **`role="presentation"` on tables** | Without this, screen readers announce every table cell as "row 1, column 2..." |
| **`<title>` tag** | Shows in browser tabs, email previews, and is read by screen readers on open. |
| **`lang` attribute** | Tells screen readers which pronunciation rules to use. |

### What we don't check (but should in production)
- Actual color contrast ratios (4.5:1 for normal text, 3:1 for large text) — needs a color contrast library
- Dark mode rendering — requires visual diffing tools like Litmus or Email on Acid
- Mobile tap target sizes (44×44px minimum for CTAs)

---

## 6. Freeform Parsing

### How it works
1. User pastes unstructured text (Slack message, meeting notes, creative brief)
2. Sent to **DeepSeek Flash** with a structured extraction prompt
3. Returns JSON with: `campaign_name`, `audience`, `goal`, `key_message`, `cta_text`, `cta_url`, `tone`, `template_type`, `event_date`, `additional_context`
4. Populates the structured form behind the scenes
5. Proceeds through normal generation pipeline

### Why this matters
Marketing briefs arrive in many formats — Slack messages, Notion docs, meeting notes, email forwards. The freeform input removes the friction of manually transcribing. In production, this could ingest directly from Slack webhooks, Jira tickets, or brief templates.

### Edge cases it handles
- Missing fields: LLM infers reasonable defaults
- No URL: defaults to `figma.com`
- Ambiguous tone: LLM picks based on context clues
- Very short input: still produces a valid brief (tested with 2-sentence inputs)

---

## 7. UI/UX Design Decisions

### Left panel → Campaign Details (post-generation)
After generating an email, the left panel transforms from "input mode" to "details mode" — showing the campaign brief as read-only fields. This mirrors ESP UX patterns (Customer.io, Braze, Iterable) where:
- **Left:** Campaign configuration / metadata
- **Right:** Content preview

It also eliminates "dead space" — the input form has no value after generation.

### Dual preview (desktop + mobile)
Email previews are rendered at actual device widths:
- **Desktop:** 600px (standard email width)
- **Mobile:** 375px (iPhone SE/6/7/8 width)

Showing both simultaneously helps catch responsive issues that are invisible in a single-width preview.

### Metadata bar
Subject line, confidence score, brand status, and template type are displayed as a compact chip bar at the top of the results — not as bulky cards. The email preview is the primary visual element. This follows the principle that **the content is the deliverable** — metadata supports it, not competes with it.

### Mode toggle (Freeform vs Structured)
- **Freeform** is the default — reflects the reality that most briefs start as unstructured text
- **Structured** is available for when the brief is already well-defined
- Toggle is at the top of the panel, easy to discover

### Password gate
Simple password protection (`nicolascage`) prevents casual access while the prototype is in development. Not real security — just enough friction to keep the demo controlled. Uses Flask sessions with `SameSite=None; Secure=True` cookies to work inside the portfolio iframe.

---

## 8. Customer.io Integration

### Sync workflow
`sync.py` handles pushing generated emails to Customer.io Design Studio:
1. Checks for `CUSTOMERIO_ENV_ID` and `CUSTOMERIO_API_KEY` environment variables
2. Creates a transactional message in Design Studio with the generated HTML, subject line, and preview text
3. Returns a preview URL so the user can open it in Customer.io for final QA

### Why Customer.io Design Studio
Design Studio is Customer.io's transactional email template editor. Pushing to it means:
- The email exists in the same system where it will be sent
- QA and approval workflows happen in the actual ESP
- No copy-paste errors from external previews
- Version history is maintained in Customer.io

### Fallback behavior
If API credentials aren't configured, the sync step is stubbed (returns a simulated success). This keeps the demo functional without requiring full Customer.io setup.

---

## 9. Deployment Architecture

### Two Vercel projects
| Project | Repo | URL | Purpose |
|---------|------|-----|---------|
| Portfolio | `andymccutcheon/andys-portfolio` | `amccutcheon.com` | Personal site |
| Email Agent | `andymccutcheon/figma-email-production-agent` | `figma-email-production-agent.vercel.app` | Prototype |

### Iframe embedding
The portfolio's `/figma` route renders a full-screen iframe loaded from the email agent's Vercel deployment. This approach:
- **Keeps deployments independent** — agent updates don't risk breaking the portfolio
- **Preserves URL structure** — `amccutcheon.com/figma` is a clean, memorable URL
- **Enables session isolation** — the agent's Flask session works independently

### Static asset serving on Vercel
Vercel's Python runtime doesn't serve static files by default. Flask handles all static file serving via `static_folder='static'`. The `vercel.json` uses a single catch-all route to the Python function. The earlier broken `/static/*` route (that tried to map to a non-existent serverless function) was removed.

### SameSite cookie fix
When embedded in an iframe on a different domain, browsers treat cookies as "third-party" and block them. Setting `SameSite=None; Secure=True` on the Flask session cookie explicitly allows cross-site cookie usage. Required because the portfolio (`amccutcheon.com`) and agent (`vercel.app`) are different origins.

---

## 10. Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Flask (Python) | Lightweight, fast to prototype, excellent for API endpoints |
| **Frontend** | Vanilla HTML/CSS/JS | No framework overhead for a single-page tool; served from Flask templates |
| **AI** | DeepSeek API (OpenAI-compatible) | High-quality output, competitive pricing, chat completions interface |
| **Email compilation** | MJML 4.x via npx | Battle-tested cross-client email rendering |
| **Design system** | CSS custom properties | Full token system (colors, shadows, radii, typography) — maintainable and consistent |
| **Fonts** | Figma Standard Text (woff2) | Authentic Figma look; loaded locally (no Google Fonts dependency) |
| **Deployment** | Vercel (Python runtime) | Auto-deploys from GitHub, HTTPS, serverless |
| **Testing** | pytest | 11 deterministic tests covering intake, brand check, and parsing |

---

## 11. Testing Strategy

### What's tested (11 tests, `tests/test_pipeline.py`)

| Category | Tests | What they verify |
|----------|-------|-----------------|
| **Intake validation** | 5 | Happy path, missing fields, CTA word limit, URL format, tone validation |
| **Brand compliance** | 5 | Logo detection, unsubscribe requirement, forbidden phrases, exclamation marks, clean email pass |
| **Markdown parsing** | 1 | Brief parsing from `.md` files |

### What's not tested (production gaps)
- LLM generation quality (non-deterministic — needs human eval)
- MJML compilation (depends on Node.js/npm — tested via integration)
- Customer.io sync (requires API credentials)
- UI interactions (needs browser test framework like Playwright)
- Accessibility compliance (needs screen reader testing)

---

## 12. Design System

The UI uses a CSS custom property token system (`:root` variables) covering:

| System | Tokens | Purpose |
|--------|--------|---------|
| **Brand palette** | `--brand-50` → `--brand-900` | Purple brand color (9-step scale) |
| **Accent colors** | Blue, green, amber, red, pink, teal | Semantic states (success, warning, error) |
| **Neutrals** | `--gray-50` → `--gray-950` | Text hierarchy, surfaces, borders |
| **Shadows** | `--shadow-xs` → `--shadow-xl` + brand glow | Depth and elevation |
| **Radii** | `--radius-sm` → `--radius-full` | Consistent border radius |
| **Typography** | `--font-sans`, `--font-mono` | Figma Standard Text + system fallbacks |
| **Transitions** | `--ease-out`, `--duration-fast/normal/slow` | Smooth, consistent motion |
| **Layout** | `--sidebar-width`, `--topbar-height` | Panel sizing |

---

## 13. Key Talking Points

### If asked "Why did you build this?"
> "Email production is one of the last manually-intensive workflows in marketing. A single campaign email can take 3-5 people across copy, design, engineering, and QA — often 2-3 days. This prototype compresses that to minutes. The goal isn't to replace humans — it's to handle the mechanical parts so creative teams can focus on strategy and taste."

### If asked "Why MJML instead of just asking the LLM for HTML?"
> "Email rendering is a uniquely hostile environment. Outlook uses Microsoft Word's engine. Gmail strips CSS. Dark mode inverts colors unpredictably. Asking an LLM to navigate that is asking for beautiful emails that break in 40% of inboxes. MJML abstracts that complexity — it's a compiler that produces table-based HTML with Outlook-specific VML conditionals. The LLM doesn't need to know about email client quirks; it just needs to produce valid MJML XML."

### If asked "How do you ensure the AI doesn't go off-brand?"
> "We don't ask the LLM to check itself — that's unreliable. All 13 brand rules are enforced in deterministic code. Regex and structural analysis catch everything from missing unsubscribe links to incorrect CTA colors. The LLM generates; the code validates. This separation is intentional — generation and validation are different concerns with different reliability requirements."

### If asked "What happens if the LLM hallucinates?"
> "Two layers of defense. First, the brand checker catches structural and content issues deterministically. Second, the confidence score — which the LLM self-reports — flags low-confidence outputs for human review. In production, you'd add a third layer: a human-in-the-loop review gate before anything reaches Customer.io."

### If asked "What would you do differently in production?"
> "Three things. One: add visual regression testing with tools like Litmus or Email on Acid to catch rendering issues across 90+ client combinations. Two: build a feedback loop — every human edit teaches the system what 'good' looks like. Three: integrate directly with the brief intake system so briefs flow into the pipeline automatically rather than being copy-pasted."

### If asked about the accessibility work
> "The Email Marketing Coalition's 2026 report found that 96% of marketing emails fail automated accessibility checks. We baked 6 accessibility rules directly into the brand checker — heading hierarchy, alt text, descriptive links, table roles, title tags, and language attributes. These aren't nice-to-haves; they're the difference between an email that 15% of recipients can actually read and one that excludes them."
