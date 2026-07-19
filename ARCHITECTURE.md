# Email Production Agent — Architecture

## Pipeline Overview

```
BRIEF INTAKE  →  GENERATE  →  BRAND CHECK  →  PREVIEW  →  SYNC (stubbed)
 (deterministic)  (LLM)       (deterministic)  (deterministic)  (deterministic)
                       ↓
                  HUMAN REVIEW GATE
                 (confidence < threshold → escalate)
```

## Step-by-step

### Step 1: Brief Intake (Deterministic)
- Parse the marketer's brief (structured JSON or natural language)
- Extract: campaign name, audience, goal, key message, CTA, assets, timeline
- Validate: required fields present, URLs resolvable, character limits checked
- Output: structured brief object
- **Why deterministic:** Schema validation against known fields. No judgment needed. If the brief is malformed, fail fast with a specific error — don't ask an LLM to guess what the marketer meant.

### Step 2: Generate (LLM Judgment)
- Input: structured brief + brand context files + email template library
- LLM produces: subject line, preview text, email body HTML (responsive, accessible), plain-text fallback
- Temperature: 0.4 (creative enough for copy, constrained enough for structure)
- **Why LLM:** Copywriting requires semantic understanding of audience, tone, and message. Subject lines require creative variation. The model adapts voice to the brief's intent.
- **What stays out of the model:** HTML structure (template-driven), brand colors/fonts (injected post-generation), legal footers (appended deterministically).

### Step 3: Brand Check (Deterministic)
- Validate generated output against brand rules:
  - Color palette compliance (hex validation)
  - Font family match
  - Logo placement and sizing
  - Required legal/footer elements present
  - Tone markers (forbidden phrases, required brand terms)
  - Accessibility: alt text on images, heading hierarchy, contrast ratios
- Output: pass/fail report with specific violations flagged
- **Why deterministic:** Brand rules are rules, not suggestions. A regex or schema check is more reliable and auditable than asking an LLM "does this look on-brand?"

### Step 4: Preview (Deterministic)
- Render HTML email in a preview page
- Show side-by-side: generated email + brand compliance report
- Human reviewer can: approve, reject, or annotate with feedback
- Feedback loops back to Step 2 for regeneration
- **Why deterministic:** Rendering is a display function. The human makes the judgment call here.

### Step 5: Sync to Customer.io (Deterministic, Stubbed)
- API call to create/schedule the email in Customer.io
- Includes: HTML body, plain text, subject line, preview text, metadata
- Stubbed in POC with clear interface contract
- **Why deterministic:** API integration. The model doesn't touch the API.

## Human-in-the-Loop Methodology

The agent escalates to a human when:
1. **Confidence below threshold:** LLM response includes a self-assessed confidence score (1-5). Below 3 → flagged in preview.
2. **Brand check failures:** Any critical violation (logo, legal, color) → preview shows red flag.
3. **Edge case detected:** Brief contains fields the agent hasn't seen before → "I need a human to review this part."
4. **Reviewer feedback loop:** Human can always reject and provide feedback for regeneration.

The key principle: **the agent does the work, the human makes the decision.** The agent never sends an email without human approval.

## Modularity

Each step is an independent, testable module:
- `intake.py` — parses and validates briefs
- `generate.py` — calls LLM, returns structured email object
- `brand_check.py` — runs deterministic validation
- `preview.py` — renders HTML preview
- `sync.py` — Customer.io integration (stubbed)
- `orchestrator.py` — wires steps together, manages state

Each module has its own test file. Each prompt has its own version. You can swap the LLM provider, change the brand rules, or replace the email template without touching anything else.
