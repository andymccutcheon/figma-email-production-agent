# Email Production Agent — Test Prompts

> Use these in Freeform mode to test different campaign types, edge cases, and the agent's parsing ability.

---

## Product Launch

### Prompt 1 — Figma Slides (detailed brief)
```
We're launching Figma Slides next Tuesday — a new way to create and share presentations directly in Figma. Target audience is product managers and design leads who already use Figma for design work. The big hook: turn any Figma frame into a slide with one click, real-time collaboration on decks, and presenter mode built in. Goal is 2,000 new Slides projects created in the first week. CTA should be "Try Figma Slides" linking to figma.com/slides. We've been in beta with 200 teams and NPS is 72. Tone should be exciting but professional — this is a major new product, not just a feature update.
```

### Prompt 2 — Minimal brief (tests parsing inference)
```
New feature: Figma AI. Let people generate UI from text prompts. CTA: Try it now.
```

### Prompt 3 — Slack-style (messy, real-world)
```
hey team, we need an email for the new auto-layout 2.0 launch. going out to all figma users who've used auto-layout at least once. main thing: it's way faster now, supports wrapping, and works with variables. CTA: see what's new → figma.com/auto-layout. tone: feature update. ship date is thursday.
```

---

## Event Invite

### Prompt 4 — Config 2026 (detailed)
```
Config 2026 is June 10-11 in San Francisco at Moscone Center. We need an early access email for past attendees and Figma power users. Early bird pricing is $399 (saves $200) and we're capping early access at the first 3,000 registrations. Keynote lineup: Dylan Field, Sho Kuwamoto, and a surprise guest from the design world. This year's theme is "Design at Scale" — workshops on design systems, AI-assisted design workflows, and cross-functional collaboration. CTA: "Register now" → config.figma.com/2026. Make it feel exclusive since this goes out before the public announcement.
```

### Prompt 5 — Virtual workshop (tone test)
```
Free virtual workshop next Wednesday: "Advanced Prototyping in Figma." 60-minute hands-on session with the Figma education team. For intermediate Figma users. Limited to 500 seats. CTA: Save your spot → figma.com/workshops/prototyping.
```

---

## Feature Update

### Prompt 6 — Dev Mode (detailed)
```
We just shipped a major update to Dev Mode — designers can now annotate specs directly on the canvas, developers get automatic code snippets in 8 languages, and there's a new VS Code extension that syncs design changes in real time. Target audience is frontend engineers and engineering managers at companies using Figma. We want 30% of Dev Mode users to try the VS Code extension in the first month. The community has been asking for better designer-to-developer handoff for years — this is our answer. CTA: "Get the extension" → figma.com/dev-mode. Include a mention that it's free for all Figma plans.
```

### Prompt 7 — Variables update (shorter)
```
Just shipped: variables now support typography and spacing tokens. Works across all component properties. This was the #1 community request. CTA: Learn more → help.figma.com/variables
```

---

## Educational / Newsletter

### Prompt 8 — Design systems report (detailed)
```
Monthly newsletter for design system teams. This month's topic: how leading teams measure design system adoption and ROI. We interviewed 15 teams including Spotify, Airbnb, and GitHub. Key insights: teams tracking component reuse see 40% faster time-to-market, the most successful teams treat their design system as an internal product with a dedicated PM, and the #1 predictor of adoption isn't tooling — it's having a Slack channel where designers and engineers actually talk to each other. CTA: "Read the full report" → figma.com/design-systems-report. Audience is design ops leaders and design system managers. Should feel like a thoughtful, research-backed newsletter — not marketing fluff.
```

### Prompt 9 — Quick tip newsletter
```
Weekly tips email. This week: 3 Figma shortcuts that save 20 minutes a day. Audience: all Figma users. Keep it light and useful. CTA: See all tips → figma.com/tips
```

---

## Re-engagement

### Prompt 10 — 90-day dormant (detailed)
```
Win-back campaign for users who haven't opened Figma in 90+ days. We want to show them what they've missed — AI features, Dev Mode, variables support, and the new performance improvements (files load 2x faster now). Offer a personal touch: mention that their team is still actively using Figma (FOMO angle). CTA: "Open Figma" → figma.com. Tone should be warm and welcoming, not guilt-trippy. Maybe lead with "A lot's happened in 3 months" and show a quick visual timeline of shipped features. Audience is dormant users at companies with active Figma seats.
```

### Prompt 11 — 30-day lapsed (softer tone)
```
Haven't seen you in a bit — just checking in. We shipped some things you might like: faster file loading, new commenting threads, and dark mode for the desktop app. CTA: Open Figma → figma.com
```

---

## Edge Cases & Stress Tests

### Prompt 12 — Bare minimum (tests parsing inference)
```
send email about figjam to teachers. CTA: try it.
```

### Prompt 13 — Long rambling input (tests extraction)
```
So I was talking to Sarah from the design systems team yesterday and she mentioned that we should really do an email about the new branching feature because customers keep asking about it in support tickets. I think the audience should be design system managers and enterprise admins. The key thing to communicate is that branching lets teams experiment with component changes without breaking production — it's basically git for design systems. We could mention that it's been in beta for 6 weeks and teams like Stripe and GitHub are already using it. Maybe frame it as "design systems are software — treat them that way." Goal is to get 200 teams to try branching in the first month. CTA: "Start branching" → figma.com/branching. Tone should be educational but authoritative.
```

### Prompt 14 — Non-Figma product (tests brand adherence)
```
We're launching a new project management tool called TaskBoard. Target audience is remote teams. Integrates with Slack and GitHub. CTA: "Get started free" → taskboard.io. Tone should be friendly and approachable. Key message: async work doesn't have to feel disconnected.
```

### Prompt 15 — Event with no date specified
```
You're invited to Figma's annual community meetup. Network with other designers, see live demos, and meet the Figma team. CTA: "RSVP here" → figma.com/community-meetup. This is informal — no formal presentations, just community.
```

---

## Structured Mode (use these in the form fields)

| Campaign | Audience | Goal | Key Message | CTA | Tone | Template |
|----------|----------|------|-------------|-----|------|----------|
| Figma AI Launch | Design leads at 50+ companies | 500 AI feature activations in week 1 | Figma AI is now available — autocomplete, text-to-design, smart layers | Try Figma AI → figma.com/ai | product_launch | product_launch |
| Config 2026 Early Access | Past attendees + power users | Early-bird signups before public announcement | Config is back — 10k+ designers, keynotes, workshops | Register now → config.figma.com/2026 | event | event_invite |
| Variables Everywhere | Component users, last 90 days | 20% adoption within 30 days | Variables now work across all component properties | Learn more → help.figma.com/variables | feature_update | feature_update |
| Design Systems at Scale | Design ops leaders | Drive engagement with DS features | Top teams treat design systems as products, not projects | Read the guide → figma.com/design-systems | educational | educational |
| We Miss You | Dormant users, 90+ days | Re-activate 15% of dormant users | A lot's happened in 3 months — come see what's new | Open Figma → figma.com | reengagement | reengagement |
