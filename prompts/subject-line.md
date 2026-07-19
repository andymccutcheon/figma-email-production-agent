# subject-line.md — v1.0

## Purpose
Generate and evaluate subject line variations for A/B testing. Separated from the main email generation prompt so it can be called independently for iteration.

## Input
- `brief`: structured brief
- `voice_and_tone`: Figma voice attributes
- `count`: number of variations (default 3)

## Instructions

Generate {count} subject line variations for the email described in the brief.

Rules:
- Each under 50 characters
- No all-caps
- Max 1 emoji per subject line
- Each should use a different approach: curiosity, direct benefit, urgency/scarcity, social proof, personal

For each variation, return:
```json
{
  "subject_line": "...",
  "approach": "curiosity|benefit|urgency|social_proof|personal",
  "character_count": N,
  "predicted_open_rate_impact": "low|medium|high",
  "rationale": "one sentence explaining why this approach fits the brief"
}
```

The predicted_open_rate_impact is a directional estimate, not a guarantee. It exists to give the marketer a data point when choosing between variations.

## Version History
- v1.0: Initial prompt.
