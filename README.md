# Email Production Agent — Cortex Plan

## Repo Structure

```
email-production/
├── prompts/              # LLM prompts — versioned, documented, testable
│   ├── email-generation.md       v1.0 — Main email generation prompt
│   ├── brand-compliance.md       v1.0 — Brand compliance review prompt
│   └── subject-line.md           v1.0 — Subject line variations prompt
├── skills/               # Reusable skill modules (factored out for cross-workflow reuse)
│   ├── email-builder/            # Composition: brief → assembled email
│   │   ├── skill.md              # What this skill does, when to use it
│   │   └── prompt.md             # The prompt (imported by workflows)
│   └── brand-validator/          # Validation: email → compliance report
│       ├── skill.md
│       └── prompt.md
├── context/              # AI-readable knowledge base (the "cortex")
│   ├── brand-guidelines.md       # Figma brand rules (colors, fonts, CTAs, required elements)
│   ├── voice-and-tone.md         # Figma voice attributes and writing mechanics
│   └── email-templates.md        # Template catalog with structure definitions
├── evals/                # Evaluation framework
│   ├── test-cases.json           # Structured test cases (happy path + edge cases)
│   └── quality-rubric.md         # What "good" looks like — subjective criteria
├── core/                 # Deterministic pipeline code
│   ├── orchestrator.py           # Pipeline coordinator
│   ├── intake.py                 # Brief parsing + validation
│   ├── generate.py               # LLM generation wrapper
│   ├── brand_check.py            # Deterministic brand validation
│   ├── preview.py                # Human review preview page
│   └── sync.py                   # Customer.io integration (stubbed)
├── tests/                # Automated tests
│   ├── test_pipeline.py          # Unit tests for each module
│   └── sample-briefs/            # Test fixtures
│       ├── brief-01.md           # Product launch
│       ├── brief-02.md           # Event invite
│       ├── brief-03.md           # Feature update
│       └── brief-bad.md          # Malformed (edge case)
├── output/               # Generated previews (gitignored)
├── ARCHITECTURE.md               # System design document
└── README.md                     # This file
```

## Versioning Strategy

Every prompt, skill, and context file is versioned independently. Changes follow this process:

1. **Propose:** Create a branch. Update the file. Increment the version in the file header.
2. **Eval:** Run the eval suite against the new prompt. Compare quality scores against baseline.
3. **Review:** PR with before/after eval results. At least one other person reviews prompt changes.
4. **Merge:** If quality holds or improves, merge. If quality regresses, iterate.
5. **Log:** Changelog in the file header documents what changed and why.

### Prompt Changelog Format (in each prompt file)
```
## Version History
- v1.2: Added FigJam-specific template. Adjusted tone for educational emails (Andrew, 2026-07-15)
- v1.1: Tightened subject line character limit from 60 to 50. Added emoji constraint. (Kyle, 2026-06-20)
- v1.0: Initial prompt. Covers all email types. (Andy, 2026-06-01)
```

## What Gets Factored Out (Reusability)

From this email production workflow, these components become reusable for other workflows:

| Component | Reusable As | Next Consumer |
|-----------|-------------|---------------|
| `brand_check.py` | `brand-validator` skill | ABM landing pages, ad copy, social posts |
| `context/brand-guidelines.md` | Shared context file | ALL content generation workflows |
| `context/voice-and-tone.md` | Shared context file | ALL content generation workflows |
| `intake.py` validation pattern | Structural pattern | Any brief/request intake workflow |
| `preview.py` review gate | UX pattern | Any human-in-the-loop workflow |

The rule: if a second workflow needs the same capability, factor it out. If only this workflow uses it, keep it local. The threshold for factoring is "does someone else need this in the next 3 months?"

## How Another Marketer Reuses This

A marketer building a new workflow (e.g., ABM landing pages) would:

1. Fork `email-production/` or start from the template
2. Import shared context: `context/brand-guidelines.md`, `context/voice-and-tone.md`
3. Import shared skills: `skills/brand-validator/` for compliance checking
4. Build new prompts: `prompts/landing-page-generation.md` for their specific output
5. Reuse the eval framework pattern: `evals/test-cases.json` with landing page test cases
6. Submit a PR if their new prompts/skills are broadly useful

They don't rebuild brand validation. They don't re-define the voice. They don't re-invent the eval pattern. They build ONLY what's unique to their workflow.
