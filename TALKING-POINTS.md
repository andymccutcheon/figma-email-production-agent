# Presentation Guide — Figma Email Production Agent

> Companion talking points for the [presentation deck](/deck).  
> **Don't read the slides verbatim.** Use this to add context, stories, and conviction.

---

## Slide 1 — Overview

**What's on screen:** Title + subtitle ("From 2-week SLA to same-day turnaround")

**What to say:**

- "This is what I built in a few hours. The goal wasn't to build a polished product — it was to prove that AI can compress the email production workflow enough to matter."
- "The real pain point here is the 2-week SLA. Marketing moves faster than that. By the time an email ships, the moment has passed."
- "What you're about to see is a working pipeline, not a slide deck about a pipeline. It runs. You can try it."

**Key numbers to have in your back pocket:**
- 40-60 emails/month at Figma scale
- 2 hours of build time per email today
- 2-3 revision rounds
- The math: ~1,050 hours/year saved — roughly half an FTE

---

## Slide 2 — Prioritization Framework

**What's on screen:** Scoring matrix + why email won + what got deprioritized

**What to say:**

- "I scored four problems across five dimensions: hours saved, revenue impact, reach, feasibility, and data readiness. Email came out at 8.9/10."
- "The key insight isn't that email won. It's that the framework forces you to be honest about why other things lost. Localization is a bigger problem, but the data isn't ready. Personas are cool, but you can't measure them."
- "This is the kind of thinking I'd bring to any agent project — not just 'what can AI do?' but 'what SHOULD it do first?'"
- "The thing I'm least sure about: brand guidelines freshness. If they're 6 months stale, the agent generates outdated email. I'd validate that in week 1 before writing any more code."

**Don't just read the table.** Talk about the methodology — how you think about prioritization.

---

## Slide 3 — Architecture Pipeline

**What's on screen:** 5-step pipeline diagram + "Where I draw the line" table

**What to say:**

- "Five discrete steps. The LLM only touches step 2 — generation. Everything else is deterministic Python code."
- "This is intentional. Brand rules are rules. A regex checking for the right hex color is more reliable than asking a model 'does this look on-brand?'"
- "The model generates copy slots — about 1KB of JSON. Python assembles that into ~10KB of production HTML. This keeps the model cheap and fast while ensuring the HTML is pixel-perfect against the Figma design system."
- "The pipeline uses DeepSeek as the primary LLM with Claude as fallback. Both are called via the same OpenAI-compatible interface, so switching providers is a one-line change."
- "The sync to Customer.io is real — it creates the email in Design Studio so QA happens in the actual ESP, not a preview page."

**Anticipate the question "Why not just ask the LLM for HTML?":**
- Email rendering is uniquely hostile — Outlook uses Word's engine, Gmail strips CSS, dark mode inverts colors
- Our HTML is table-based, derived from 4 real Figma production emails in `figma-examples/`
- The copy-slots pattern means the LLM never touches HTML structure — it only writes copy

---

## Slide 4 — POC Demo

**What's on screen:** Screenshot + description + link

**What to say:**

- "This is the live prototype at amccutcheon.com/figma. If you're taking notes, go there after."
- "The flow: load a sample brief or paste freeform text → hit Generate → DeepSeek returns copy slots → Python assembles HTML → brand checker runs 13 deterministic rules → preview renders → sync to Customer.io."
- "It handles 5 template types: product launch, event invite, feature update, educational newsletter, and re-engagement. Each maps to a real Figma production email archetype."
- "The freeform input is the part I'm most proud of. You can paste a Slack message, meeting notes, or a creative brief — the agent parses it into a structured brief automatically using DeepSeek Flash."
- "What I left for later: A/B subject line testing, a proper feedback loop, send-time optimization, and visual regression testing with Litmus or Email on Acid."

**If someone asks to see it live:** Navigate to amccutcheon.com/figma, load the "Figma AI Launch" sample, hit Generate, and walk through the output. Password is `nicolascage`.

---

## Slide 5 — Cortex / Repo Plan

**What's on screen:** Reusability matrix + ABM reuse example

**What to say:**

- "I'm treating this like a product, not a one-off script. Everything is versioned, documented, and built to be reused."
- "The reusability matrix shows what carries forward: brand_check.py becomes a reusable validator for ANY content workflow. The voice-and-tone and brand-guidelines context files feed into every future agent."
- "The asset pool — `asset_pool.py` — rotates through ~20 Figma production images so emails don't all look the same. Different campaigns get different hero images and row icons, but the rotation is deterministic within the hour so the same campaign looks consistent."
- "Here's the real test: if someone else picks this up to build an ABM landing page agent, they don't rebuild brand validation. They don't re-define the voice. They fork the repo, import the shared context, write ONE new prompt, and ship. Build time drops from 3-4 weeks to maybe 1."

---

## Slide 6 — Evaluation & Reliability

**What's on screen:** Three failure modes table

**What to say:**

- "Measurement isn't optional — it's how I know what to retire."
- "I identified three failure modes and built defenses for each: bad briefs fail fast in intake validation, low-confidence outputs get flagged with a ⚠ in preview, and brand violations are caught deterministically before anything reaches Customer.io."
- "The brand checker has 13 rules and runs in milliseconds — no API call needed. It catches everything from missing unsubscribe links to wrong CTA colors to forbidden phrases."
- "The key principle: the agent does the work, the human makes the decision. Nothing sends without human approval."
- "In production, I'd add a fourth layer: visual regression testing across 90+ email client combinations using Litmus or Email on Acid."

---

## Slide 7 — Success Metrics

**What's on screen:** Today vs. With Agent comparison + hours saved + revenue impact

**What to say:**

- "These are measured, not asserted. The baseline comes from the take-home brief: 40-60 emails/month, 2 hours each, 2-3 revision rounds."
- "With the agent: 15 minutes of marketer time per email. Brief → QA in under an hour. Zero brand compliance failures because the checker runs on every output."
- "The annual math: ~1,050 hours saved — about half an FTE. But the revenue impact is the bigger number. No SLA means more campaigns ship. Faster testing means A/B tests ship in days, not weeks."
- "Measurement plan: Customer.io send volume and attributed conversions, 6 months pre vs. post. You can't improve what you don't measure."

---

## Slide 8 — Adoption Plan

**What's on screen:** 3-phase rollout timeline

**What to say:**

- "Shipping the agent is 50% of the work. Making marketers actually use it is the other 50%."
- "Phase 1: find ONE person who feels the 2-week SLA most acutely. Walk through their actual next email — not a demo. Goal: one real email shipped with zero hand-holding."
- "Phase 2: that person becomes your champion. 'I built an email in 15 minutes.' Group walkthrough with real briefs from the team's backlog."
- "Phase 3: brief intake form goes live for everyone. Email team shifts from builder to QA reviewer. Goal: 50% of monthly volume through the agent."
- "This is the adoption pattern I used at Block. Start with one believer, let the results speak, then open the gates."

---

## Slide 9 — Next Steps

**What's on screen:** Three columns — Immediate, Next Agent, Platform Vision

**What to say:**

- "The first agent is the hardest. The second one takes half the time because the cortex is already built."
- "Immediate next steps: validate brand guidelines are current, add a human annotation feedback loop, and add visual regression testing."
- "The next agent: ABM landing pages. Brand validation, review gate, and eval framework are already reusable. Build time drops from 3-4 weeks to maybe 1."
- "The platform vision: each new agent adds to the shared cortex instead of being its own silo. The goal isn't 10 agents — it's a system where building the 11th takes an afternoon."

---

## Slide 10 — Closing

**What's on screen:** Two quotes + invitation to dig in

**What to say:**

- "At Block, I shipped 10 agents, drove 73% adoption, and built the infrastructure layer that made the 11th agent easy. I know what it takes to go from POC to platform."
- "At Figma, I'd start with email — and then make it the first tile in a system that makes every marketer faster."
- "I'm happy to dig into any part of this. Especially the parts I'm least sure about. That's where the interesting conversations happen."

**If you get the "what would you do differently?" question:**
- Visual regression testing (Litmus/Email on Acid) for 90+ client combos
- Feedback loop where every human edit teaches the system
- Direct integration with the brief intake system (Slack, Notion, Jira) so briefs flow automatically
- A/B testing infrastructure built into the pipeline rather than bolted on

**If you get the "how do you stay on brand?" question:**

Don't just say "I used the brand guidelines." Walk through the four sources:

1. **Figma's actual brand guidelines** — colors (`#0D99FF`, `#5551FF`, the full 27-color palette), fonts (Whyte, Inter, Helvetica Neue), logo requirements. These are in `context/brand-guidelines.md` — the same doc the LLM reads for generation. The checker enforces what the LLM was told to produce.

2. **Figma's voice and tone guide** — forbidden phrases like "game-changing" and "revolutionary" came directly from `context/voice-and-tone.md`. Figma's brand voice is confident but not hyperbolic. The checker catches words that undermine that.

3. **Four real Figma production emails** — I reverse-engineered the structural patterns from `figma-examples/`. That's where the CTA color rules came from: production lifecycle emails use `#5551FF`, newsletters use `#000000`. I didn't invent those — I observed them.

4. **The Email Marketing Coalition's 2026 accessibility report** — 96% of marketing emails fail automated accessibility checks. Six of the 16 rules are accessibility rules (heading hierarchy, alt text, descriptive links, table roles, title tags, language attributes). These aren't "nice to have" — they're the difference between an email 15% of recipients can read and one they can't.

**The key framing:** "I don't ask the LLM if it stayed on-brand — that's asking a creative tool to audit itself. Every check is a regex, a hex code match, or a structural pattern. It runs in milliseconds, it's reproducible, and it can't hallucinate. The LLM generates; the code validates."

**If you get the "will this replace designers?" question:**
- No. It handles the mechanical parts — copy assembly, HTML construction, brand checking
- Designers and copywriters focus on strategy, taste, and the creative direction
- The agent is a force multiplier, not a replacement
