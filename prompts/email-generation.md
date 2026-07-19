# email-generation.md — v2.0 (MJML + Accessibility)

## Purpose
Generate a complete marketing email (subject line, preview text, MJML body, plain text) from a structured brief and brand context. Output is compiled to cross-client HTML via MJML.

## Output Format
Return a JSON object with these fields:
```json
{
  "subject_line": "...",
  "preview_text": "...",
  "html_body": "<mjml>...</mjml>",
  "plain_text": "...",
  "template_used": "...",
  "confidence_score": 1-5
}
```

**Critical: The `html_body` field MUST contain valid MJML XML**, not raw HTML. It will be compiled to HTML automatically after generation. Start with `<mjml>` and end with `</mjml>`.

## MJML Structure Rules

Every generated email must follow this MJML document structure:

```xml
<mjml lang="en">
  <mj-head>
    <mj-title>Campaign Name</mj-title>
    <mj-attributes>
      <mj-all font-family="'Helvetica Neue', Arial, sans-serif" />
      <mj-text font-size="16px" color="#1E1E1E" line-height="1.6" />
      <mj-button background-color="#0D99FF" color="#FFFFFF" font-weight="600" border-radius="8px" padding="14px 32px" font-size="16px" />
    </mj-attributes>
    <mj-style inline="inline">
      .footer-text { color: #666666; font-size: 12px; }
    </mj-style>
  </mj-head>
  <mj-body background-color="#F5F5F5">
    <!-- content -->
  </mj-body>
</mjml>
```

### MJML Engineering Rules (MUST follow)
1. **All visual content in `<mj-column>` inside `<mj-section>`.** Sections cannot be nested. Sections cannot be inside columns.
2. **Use `<mj-section>` for horizontal rows.** Use `<mj-column>` for vertical stacks within a section.
3. **Do not nest `<mj-section>` inside another `<mj-section>`.**
4. **Always use `<mjml lang="en">` as the root element.**
5. **Use `<mj-title>` for the email title (populates `<title>` and `aria-label`).**
6. **All `<mj-image>` must have `alt` attribute.** Use `alt="Figma"` for the logo. Use descriptive alt text for content images.
7. **Use `<mj-button>` for CTAs** — never raw `<a>` tags.
8. **Always include:**
   - Logo: `<mj-image src="LOGO_URL" alt="Figma" width="40px" align="center" />`
   - View-in-browser link at top
   - Unsubscribe link in footer
   - Physical address: "Figma, Inc. 760 Market St, San Francisco, CA 94102"
9. **600px max width** — handled automatically by MJML, don't set widths manually.

### Accessibility Rules (MUST follow)
1. **alt on every image.** Content images: descriptive alt. Logo: `alt="Figma"`. Decorative: `alt=""`.
2. **Single `<h1>`.** Use `<mj-text font-weight="700" font-size="28px">` for the main heading (acts as h1 visually). Don't use multiple large headline-equivalent texts.
3. **Descriptive link text.** CTA button text must say what happens: "Register for Config" not "Click here". Never use "click here" or "read more" as the only link text.
4. **Heading hierarchy.** Don't jump from a large headline directly to tiny text without intermediate sizing.
5. **4.5:1 contrast minimum.** Don't use light gray (#999999) on white (#FFFFFF). Body text on white should be #1E1E1E minimum.

## Subject Line Rules
- Under 50 characters
- No all-caps. Max 1 emoji.
- Action-oriented or curiosity-driven
- Reflect the brief's tone

## Preview Text Rules
- Under 90 characters
- Complements the subject line — don't repeat it
- Gives a reason to open

## Plain Text Rules
- Clean, readable text version
- Links written out in full
- No formatting that won't render in plain text

## Voice Rules (from voice_and_tone)
- Clear over clever
- No forbidden phrases (see brand guidelines)
- Write like a smart colleague, not a press release

## Confidence Score
5 = highly confident, output is clean and on-brand. 1 = unsure about content quality, brand alignment, or output structure. Be honest — low confidence is better than wrong.

## Version History
- v2.0: Switched to MJML output. Added accessibility rules. Added engineering rules.
- v1.0: Initial prompt.
