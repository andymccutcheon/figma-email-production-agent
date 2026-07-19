# brand-compliance.md — v1.0

## Purpose
Validate a generated email against Figma brand rules. This prompt is used as a secondary check after deterministic validation — it catches what regex can't: tone, visual coherence, and subjective brand fit.

## Input
- `email_html`: the generated HTML email
- `brand_guidelines`: Figma brand rules
- `voice_and_tone`: Figma voice attributes

## Instructions

Review this email for brand compliance. Focus on what automated checks MISS:

1. **Visual brand fit:** Does it FEEL like Figma? Clean, modern, restrained. Not busy or loud.
2. **Voice consistency:** Does the copy sound like the Figma voice attributes? Clear, confident, helpful, human.
3. **CTA appropriateness:** Is the CTA action-first and 2-4 words? Does it match the email's intent?
4. **Forbidden phrases:** Check for any forbidden phrases from voice_and_tone.
5. **Overall coherence:** Does the email hold together as a single message, or does it feel like stitched-together sections?

Return JSON:
```json
{
  "overall_pass": true/false,
  "issues": [
    {
      "severity": "critical|warning|suggestion",
      "location": "subject_line|preview|body|cta",
      "description": "specific, actionable issue"
    }
  ],
  "score": 1-10,
  "summary": "one-sentence overall assessment"
}
```

If overall_pass is false, the email should be flagged for human review regardless of other checks.

## Version History
- v1.0: Initial prompt.
