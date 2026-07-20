# Figma Slides Deck — Outline

**Presentation:** 30 minutes + 15 min Q&A
**Audience:** Andrew Mattock (Hiring Manager), Kyle Ketchum (Technical Reviewer)

---

## Slide 1: Title
**What Andy McCutcheon Built for the Email Production Problem**

*Subtitle: From 2-week SLA to same-day turnaround — a working agent that turns a brief into a ready-to-review email*

---

## Slide 2: The Prioritization Framework

**Headline:** Which problem do you solve first? It depends on what you optimize for.

**Framework:** I scored all four opportunities across five dimensions:

| Dimension | Weight | Why it matters |
|-----------|--------|----------------|
| Hours saved / year | 25% | Direct efficiency gain |
| Revenue impact | 25% | Pipeline or conversion lift |
| Reach (marketers/regions) | 20% | How many people get faster |
| Build feasibility | 15% | Can we ship a working agent in <2 weeks |
| Data availability | 15% | Do we have the inputs, or do we need to build data infrastructure first |

**Scoring:**

| Story | Hours | Revenue | Reach | Feasibility | Data | Total |
|-------|-------|---------|-------|-------------|------|-------|
| ① Content Localization | 8/10 | 8/10 | 7/10 | 3/10 | 5/10 | 6.6 |
| ② ABM Landing Pages | 7/10 | 9/10 | 5/10 | 7/10 | 7/10 | 7.0 |
| ③ Email Production | 10/10 | 8/10 | 9/10 | 8/10 | 9/10 | **8.9** |
| ④ Living Personas | 5/10 | 4/10 | 6/10 | 5/10 | 4/10 | 4.9 |

**Recommendation: Email Production.** Why it wins:
- Highest hours-saved ceiling (960-1,440 hrs/yr)
- Touches nearly every marketer who sends email
- The 2-week SLA is a hard cap on throughput — removing it unlocks revenue beyond the efficiency gain
- The data we need (brand guidelines, brief format, email templates) already exists
- It's the fastest path to an agent that's live, adopted, and measurable

**What I deprioritized and why:**
- Localization: too many asset types for a v1 agent. Build email first, then extend the pipeline.
- ABM pages: strong #2. Would build second — the brand validation module from email production is directly reusable.
- Personas: highest technical risk, hardest to measure. Right problem, wrong moment.

**Assumption I'm least confident about:** That the brand guidelines and voice/tone docs are current and comprehensive. If they're 6 months stale, the agent generates on-brand-according-to-outdated-docs email — which is worse than off-brand. I'd validate in week 1.

---

## Slide 3: Architecture — The Pipeline

**Headline:** Five discrete steps. The model only touches what genuinely needs judgment.

```
BRIEF INTAKE  →  GENERATE  →  BRAND CHECK  →  PREVIEW  →  SYNC
 (code)          (LLM)        (code)          (code)      (stubbed)
                      ↓
                 HUMAN REVIEW GATE
```

**Where the line is — and why:**

| Step | Deterministic or LLM? | Why |
|------|----------------------|-----|
| Brief intake & validation | Deterministic (Python) | Schema validation against known fields. If the brief is malformed, fail fast with a specific error — don't ask a model to guess. |
| Email generation (copy + HTML) | LLM (Claude) | Copywriting requires semantic understanding of audience, tone, and message. Subject lines require creative variation. This IS judgment work. |
| Brand compliance check | Deterministic (Python) | Brand rules are rules. A regex checking for #7B61FF is more reliable than asking a model "does this look on-brand?" |
| Preview rendering | Deterministic (HTML) | Display function. The human makes the judgment here — not the model. |
| Sync to Customer.io | Deterministic (API) | API integration. The model never touches the API. |

**Modularity:** Each step is an independent Python module with its own test file. You can swap the LLM, change the brand rules, or replace the email template without touching anything else.

---

## Slide 4: POC Demo

**Headline:** It runs. Here's what the critical path does.

[Live demo or screen recording — 2-3 minutes]

Demo flow:
1. Show the sample brief (brief-01.md)
2. Run `python3 main.py --sample 1`
3. Walk through the output:
   - Parsed brief (validated, structured)
   - Generated email (subject, preview, HTML)
   - Brand compliance report (passed, 1 warning about CTA color)
   - Preview page (human review gate)
4. Show the preview HTML in a browser
5. Note: Customer.io sync is stubbed — the interface contract is defined and documented

**What I deliberately scoped out:**
- Real Customer.io API integration (stubbed with documented interface)
- Multi-variant A/B subject line generation (prompt exists in `subject-line.md`, not wired into main flow)
- Feedback loop (human annotations → regeneration) — the architecture supports it, not built in POC
- Email scheduling and send-time optimization

---

## Slide 5: Cortex / Repo Plan

**Headline:** Treated like a product — versioned, documented, and built for reuse.

**Folder structure:** (show the repo tree)

**Versioning:** Every prompt has a version header and changelog. Changes go through PR with eval results attached. If quality regresses, the PR doesn't merge.

**What gets factored out for the next workflow:**

| From email production | Reusable as | Next consumer |
|----------------------|-------------|---------------|
| `brand_check.py` | `brand-validator` skill | ABM landing pages, ads, social |
| `brand-guidelines.md` | Shared context | ALL content workflows |
| `voice-and-tone.md` | Shared context | ALL content workflows |
| `intake.py` pattern | Structural pattern | Any brief/request intake |
| `preview.py` review gate | UX pattern | Any human-in-the-loop flow |

**How another marketer reuses this for ABM pages:**
1. Fork the repo
2. Import shared context & skills (brand, voice)
3. Write ONE new prompt for landing page generation
4. Reuse the eval framework pattern
5. Ship

They don't rebuild brand validation. They don't re-define the voice. They build ONLY what's unique.

---

## Slide 6: Evaluation & Reliability

**Headline:** Measurement isn't optional — it's how you know what to retire.

### Error Handling — Three Failure Modes

| Failure mode | How we catch it | What happens |
|-------------|----------------|-------------|
| **Structured input error** (bad brief) | Deterministic validation in intake | Fails fast with specific error. Agent says "I need these fields: audience, goal, CTA." Does not call the LLM. |
| **Low-confidence generation** | LLM self-assesses 1-5 confidence score | Score ≤ 3 → preview page shows ⚠ flag. Human makes the call. |
| **Brand violation** (silent failure) | Deterministic brand checker runs on every output | Critical violations block sync. Warnings are shown in preview. Human approves or rejects. |

### Human-in-the-Loop Methodology

The agent escalates to a human when:
1. Confidence score ≤ 3 (LLM isn't sure about quality)
2. Any critical brand violation (logo, legal, font)
3. The brief contains fields the agent hasn't seen before

**Principle:** The agent does the work. The human makes the decision. The email NEVER sends without explicit human approval.

### Concrete Test Cases (from evals/test-cases.json)

| Test | What it validates |
|------|-------------------|
| TC-001: Product launch happy path | Full pipeline from valid brief → compliant email |
| TC-004: Malformed brief | Intake fails fast with specific errors, never calls LLM |
| TC-005: Forbidden phrases | Brand checker flags "revolutionary", "game-changing" etc. |
| TC-006: CTA too long | Validated BEFORE generation, not after |

---

## Slide 7: Success Metrics

**Headline:** Hours saved and revenue driven — measured, not asserted.

### Baseline (Today)

| Metric | Current | Source |
|--------|---------|--------|
| Email turnaround SLA | 14 days | Team data |
| Build time per email | 2 hours | Team data |
| Revision rounds per email | 2-3 rounds | Team estimate |
| Emails per month | 40-60 | Team data |

### Target (With Agent)

| Metric | Target | How we measure |
|--------|--------|---------------|
| Time from brief → ready for QA | <1 hour | Pipeline timestamp delta |
| Marketer time per email | 15 min (review only) | Time from preview open → approve |
| Revision rounds | 0-1 | Feedback loop count |
| Brand compliance | 100% on critical rules | Automated check pass rate |
| Email throughput | Uncapped (SLA eliminated) | Monthly send volume |

### Hours Saved

- **Per email:** 2 hours build → 15 min review = **1.75 hours saved**
- **Per month:** 50 emails × 1.75 hrs = **87.5 hours returned to the org**
- **Per year:** **~1,050 hours** — roughly half an FTE returned to higher-leverage work

### Revenue Driven

- **More campaigns:** SLA removed → send volume increases. Even 10% more emails × historical email conversion rates = measurable pipeline lift.
- **Faster testing:** Same-day turnaround means A/B tests ship in days, not weeks.
- **Measurement approach:** Instrument Customer.io send volume and attributed conversions. Compare pre-agent (6-month baseline) vs. post-agent.

---

## Slide 8: Adoption Plan

**Headline:** Shipping the agent is 50% of the work. Making marketers use it is the other 50%.

### Week 1-2: Pilot with One Email Team Member
- Find the person who feels the 2-week SLA most acutely
- Walk through their actual next email — not a demo, THEIR work
- They watch it generate. They review. They approve.
- **Goal:** One email shipped through the agent, by the marketer, with zero hand-holding

### Week 3-4: Expand to Full Email Team
- That first marketer is your champion. They tell the team: "I did an email in 15 minutes."
- Group walkthrough with real briefs from the team's backlog
- **Goal:** 5+ emails shipped through the agent

### Week 5-8: Open to Stakeholders
- Brief intake form goes live. Any marketer can submit a brief.
- Email team does final QA (not full build — just review)
- **Goal:** 50% of monthly email volume through the agent

### How We Know It's Adopted (Not Just Shipped)

| Signal | Threshold |
|--------|-----------|
| % of emails using agent | >70% within 8 weeks |
| Average time-to-approve | <30 minutes |
| Stakeholder NPS on turnaround | >8/10 (baseline: probably 4-5) |
| Email team reports "I have time for strategy now" | Qualitative, but critical |

### If Adoption Stalls
- I don't guess. I talk to 5 people who didn't adopt.
- Is it discoverability? Trust? Friction? Each has a different fix.
- At Block, I used K-means cohort segmentation to find the "stuck" group — they weren't resistant, they just needed a 10-minute walkthrough with their actual work.

---

## Slide 9: What I'd Do Next

**Headline:** The first agent is the hardest. The second one takes half the time.

### Immediate (Next 2 Weeks)
- Validate brand guideline freshness with the brand team
- Wire up real Customer.io API integration (the sync contract is already defined)
- Add the feedback loop (human annotations → targeted regeneration instead of full rebuild)

### Next Agent Candidate: ABM Landing Pages
- The brand validation module is already reusable
- The preview/review gate is already reusable
- The eval framework pattern is already reusable
- Estimated build time: 1 week (vs. 3-4 for the email agent, because half the infrastructure is shared)

### Platform Vision (3-6 Months)
- Each new agent adds to the shared cortex, not a new silo
- Skills → composable building blocks that any marketer can combine
- The goal isn't 10 agents. It's a system where building the 11th agent takes an afternoon, because all the infrastructure already exists.

---

## Slide 10: Closing

**Headline:** This is the role.

**What I showed:**
- A real, working agent that turns a brief into a ready-to-review email
- Architecture with a clear line between deterministic logic and LLM judgment
- Brand compliance enforced in code, not in prompts
- A human-in-the-loop gate that never lets the agent send without approval
- A cortex structure designed for reuse, not one-off
- Metrics that measure hours saved and revenue driven
- A credible adoption plan grounded in how marketers actually work

**At Block, I shipped 10 agents, drove 73% adoption, and built the infrastructure layer that made the 11th agent easy.**

**At Figma, I'd start with email — and then make it the first tile in a platform that makes every marketer faster.**

**I'm happy to dig into any part of this. Especially the parts I'm least sure about.**
