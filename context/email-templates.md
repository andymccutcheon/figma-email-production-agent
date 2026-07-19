# Email Templates (MJML)

> Template structures for common Figma email types. All templates are built in MJML.
> The LLM selects and populates based on the brief, outputting valid MJML XML.

## Required Elements (every template)

All MJML documents must include:
1. `<mjml lang="en">` root
2. `<mj-head>` with `<mj-title>`, `<mj-attributes>`, and `<mj-style>`
3. Logo: `<mj-image src="LOGO_URL" alt="Figma" width="40px" align="center" />`
4. View-in-browser link in first `<mj-section>`
5. Footer `<mj-section>` with unsubscribe, preferences, and physical address
6. All images have `alt` attribute

The logo URL is: `https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png`

## Template: Product Launch
Structure:
- Hero section with campaign name (28px bold) and key message
- `<mj-button>` CTA with brief.cta_text
- Feature highlights section (background-color="#F5F5F5")
  - 3 features, each with bold title + description text
- Standard footer

## Template: Event Invite
Structure:
- Hero section with background-color="#0D99FF"
  - "You're invited" label (uppercase, 14px, white at 80% opacity)
  - Event name (28px bold, white)
  - Event date (18px, white at 90% opacity)
- "Why attend" section with bullet points
- `<mj-button>` CTA
- Standard footer

## Template: Feature Update
Structure:
- "New in Figma" label (uppercase, 14px, #0D99FF)
- Feature name (28px bold)
- Key message description
- "What changed" section (background-color="#F5F5F5")
  - 2 feature bullets with title + description
- `<mj-button>` CTA
- Standard footer

## Template: Educational / Newsletter
Structure:
- Campaign name (28px bold)
- Key message description
- "What we're thinking about" section (background-color="#F5F5F5")
  - 1-2 paragraphs of educational content
  - Optional: community highlight or tip
- `<mj-button>` CTA
- Standard footer

## Template: Re-engagement
Structure:
- Warm headline: "A lot's happened" / "We'd love to have you back"
- What's new section with 2-3 feature bullets
- `<mj-button>` CTA: "Open Figma" or similar
- Standard footer
