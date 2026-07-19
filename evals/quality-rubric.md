# Quality Rubric — Email Production Agent

## What "Good" Output Looks Like

### Subject Line
- [ ] Under 50 characters
- [ ] No ALL CAPS
- [ ] Max 1 emoji
- [ ] Reflects the brief's tone
- [ ] Action-oriented or curiosity-driven

### Preview Text
- [ ] Under 90 characters
- [ ] Complements subject line (doesn't repeat it)
- [ ] Gives a reason to open

### HTML Body
- [ ] Max width 600px, mobile-friendly
- [ ] Figma logo at top, linked
- [ ] Correct brand colors (#000000, #7B61FF, #666666, #F5F5F5, #FFFFFF)
- [ ] Correct font stack (Helvetica Neue, Arial, sans-serif)
- [ ] CTA button: #7B61FF background, 8px border-radius, 14px 32px padding
- [ ] All images have alt text
- [ ] Unsubscribe link in footer
- [ ] Physical address in footer
- [ ] View in browser link
- [ ] Short paragraphs (2-3 sentences)
- [ ] No forbidden phrases

### Plain Text
- [ ] Clean, readable
- [ ] Links written out in full
- [ ] Matches HTML content

### Brand Voice
- [ ] Clear over clever
- [ ] Confident, not boastful
- [ ] No forbidden phrases
- [ ] Appropriate tone for email type

## Confidence Score Guide

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | Highly confident. Output is clean and on-brand. | Standard review. |
| 4 | Confident. Minor concerns about tone or phrasing. | Standard review. |
| 3 | Moderate. Some sections may need adjustment. | Flag for closer human review. |
| 2 | Low. Significant concerns about quality or brand fit. | Escalate. Expect regeneration. |
| 1 | Very low. Output may be wrong or inappropriate. | Do not use. Rebuild from brief. |

Score of 3 or below → escalated in preview with a flag.
