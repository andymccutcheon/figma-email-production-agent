"""
Flask web app for the Email Production Agent.
Wraps the existing pipeline modules for a browser-based demo.
"""

import os
import sys
import json

# Load .env before imports so generate.py picks it up
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Ensure parent directory is on path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secrets
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from intake import EmailBrief
from generate import (
    generate_email,
    GeneratedEmail,
    get_active_provider,
    generate_subject_variations,
    DEEPSEEK_API_KEY,
    DEEPSEEK_FLASH_MODEL,
    _call_deepseek,
)
from brand_check import BrandChecker, BrandCheckReport
from preview import render_preview

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True,
)

ACCESS_PASSWORD = "nicolascage"


def require_auth(f):
    """Decorator that redirects to login if not authenticated (for page routes)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def require_auth_api(f):
    """Decorator that returns 401 JSON if not authenticated (for API routes)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

SAMPLE_BRIEFS = {
    # ── Product Launch ──
    "product_launch": {
        "campaign_name": "Figma AI Launch",
        "audience": "Design leads and heads of design at companies with 50+ employees",
        "goal": "Drive trial signups for Figma AI features. We want 500 new AI feature activations in the first week.",
        "key_message": "Figma AI is now available — autocomplete your designs, generate variations from text prompts, and let AI handle the tedious layers so you can focus on the creative work.",
        "cta_text": "Try Figma AI",
        "cta_url": "https://figma.com/ai",
        "tone": "product_launch",
        "template_type": "product_launch",
        "additional_context": "This is our biggest launch of Q3. The AI features have been in beta for 3 months with overwhelmingly positive feedback.",
        "freeform_text": "We're launching Figma AI — autocomplete your designs, generate variations from text prompts, and let AI handle the tedious layers. Target audience is design leads at companies with 50+ employees. Goal is 500 new AI feature activations in the first week. CTA: Try Figma AI → https://figma.com/ai. This has been in beta for 3 months with overwhelmingly positive feedback. Tone should be exciting and forward-looking.",
    },
    "slides_launch": {
        "campaign_name": "Figma Slides Launch",
        "audience": "Product managers and design leads who already use Figma",
        "goal": "2,000 new Slides projects created in the first week",
        "key_message": "Turn any Figma frame into a slide with one click — real-time collaboration on decks, and presenter mode built in.",
        "cta_text": "Try Figma Slides",
        "cta_url": "https://figma.com/slides",
        "tone": "product_launch",
        "template_type": "product_launch",
        "additional_context": "Launching next Tuesday. Beta with 200 teams, NPS 72. This is a major new product, not just a feature update.",
        "freeform_text": ("We're launching Figma Slides next Tuesday — a new way to create and share presentations directly in Figma. "
                         "Target audience is product managers and design leads who already use Figma for design work. "
                         "The big hook: turn any Figma frame into a slide with one click, real-time collaboration on decks, and presenter mode built in. "
                         "Goal is 2,000 new Slides projects created in the first week. "
                         "CTA should be 'Try Figma Slides' linking to https://figma.com/slides. "
                         "We've been in beta with 200 teams and NPS is 72. "
                         "Tone should be exciting but professional — this is a major new product, not just a feature update."),
    },

    # ── Event ──
    "event": {
        "campaign_name": "Config 2026 Early Access",
        "audience": "Past Config attendees and Figma power users in US and Europe",
        "goal": "Drive early-bird registrations before the general public announcement",
        "key_message": "Config is back. Join 10,000+ designers and builders in San Francisco for two days of keynotes, workshops, and the future of design tools.",
        "cta_text": "Register early",
        "cta_url": "https://config.figma.com/2026",
        "tone": "event",
        "template_type": "event_invite",
        "event_date": "June 10-11, 2026",
        "additional_context": "Early bird pricing is $399 (saves $200). Keynote speaker lineup announced next week.",
        "freeform_text": ("Config 2026 is June 10-11 in San Francisco at Moscone Center. "
                         "We need an early access email for past attendees and Figma power users. "
                         "Early bird pricing is $399 (saves $200) and we're capping early access at the first 3,000 registrations. "
                         "Keynote lineup: Dylan Field, Sho Kuwamoto, and a surprise guest from the design world. "
                         "This year's theme is 'Design at Scale' — workshops on design systems, AI-assisted design workflows, and cross-functional collaboration. "
                         "CTA: 'Register now' → https://config.figma.com/2026. "
                         "Make it feel exclusive since this goes out before the public announcement."),
    },
    "workshop": {
        "campaign_name": "Advanced Prototyping Workshop",
        "audience": "Intermediate Figma users",
        "goal": "Fill 500 seats for the live workshop",
        "key_message": "Join the Figma education team for a 60-minute hands-on prototyping session. Limited to 500 seats.",
        "cta_text": "Save your spot",
        "cta_url": "https://figma.com/workshops/prototyping",
        "tone": "educational",
        "template_type": "event_invite",
        "event_date": "Next Wednesday",
        "additional_context": "Free virtual workshop. 60 minutes, hands-on.",
        "freeform_text": ("Free virtual workshop next Wednesday: 'Advanced Prototyping in Figma.' "
                         "60-minute hands-on session with the Figma education team. "
                         "For intermediate Figma users. Limited to 500 seats. "
                         "CTA: Save your spot → https://figma.com/workshops/prototyping."),
    },

    # ── Feature Update ──
    "feature_update": {
        "campaign_name": "Variables Everywhere",
        "audience": "All Figma users who have used components in the last 90 days",
        "goal": "Drive adoption of the new variables system. Target: 20% of component users try variables within 30 days.",
        "key_message": "Variables now work across all component properties — colors, text, visibility, and layout. Build one component, deploy it everywhere.",
        "cta_text": "Learn more",
        "cta_url": "https://help.figma.com/variables",
        "tone": "feature_update",
        "template_type": "feature_update",
        "additional_context": "This was our #1 community request. The old system only supported color variables.",
        "freeform_text": ("We just shipped a major update to Variables — they now support typography and spacing tokens and work across all component properties. "
                         "This was the #1 community request. Target: 20% of component users try the new system within 30 days. "
                         "CTA: 'Learn more' → https://help.figma.com/variables. "
                         "Audience is all Figma users who've used components in the last 90 days."),
    },
    "dev_mode": {
        "campaign_name": "Dev Mode 2.0",
        "audience": "Frontend engineers and engineering managers at companies using Figma",
        "goal": "30% of Dev Mode users try the VS Code extension in the first month",
        "key_message": "Designers can annotate specs directly on canvas, developers get automatic code snippets in 8 languages, and a new VS Code extension syncs design changes in real time.",
        "cta_text": "Get the extension",
        "cta_url": "https://figma.com/dev-mode",
        "tone": "feature_update",
        "template_type": "feature_update",
        "additional_context": "The community has been asking for better designer-to-developer handoff for years — this is our answer. Free for all Figma plans.",
        "freeform_text": ("We just shipped a major update to Dev Mode — designers can now annotate specs directly on the canvas, "
                         "developers get automatic code snippets in 8 languages, and there's a new VS Code extension that syncs design changes in real time. "
                         "Target audience is frontend engineers and engineering managers at companies using Figma. "
                         "We want 30% of Dev Mode users to try the VS Code extension in the first month. "
                         "The community has been asking for better designer-to-developer handoff for years — this is our answer. "
                         "CTA: 'Get the extension' → https://figma.com/dev-mode. Include a mention that it's free for all Figma plans."),
    },

    # ── Educational / Newsletter ──
    "educational": {
        "campaign_name": "Design Systems at Scale",
        "audience": "Design system teams and design ops leaders",
        "goal": "Share best practices for scaling design systems. Drive engagement with Figma's design system features.",
        "key_message": "The best teams treat design systems as products, not projects. Here's how they do it — and how Figma helps.",
        "cta_text": "Read the guide",
        "cta_url": "https://figma.com/design-systems",
        "tone": "educational",
        "template_type": "educational",
        "additional_context": "Based on interviews with 50+ design system teams. Includes real examples from Stripe, Spotify, and Airbnb.",
        "freeform_text": ("Monthly newsletter for design system teams. "
                         "This month's topic: how leading teams measure design system adoption and ROI. "
                         "We interviewed 15 teams including Spotify, Airbnb, and GitHub. "
                         "Key insights: teams tracking component reuse see 40% faster time-to-market, "
                         "the most successful teams treat their design system as an internal product with a dedicated PM, "
                         "and the #1 predictor of adoption isn't tooling — it's having a Slack channel where designers and engineers actually talk to each other. "
                         "CTA: 'Read the full report' → https://figma.com/design-systems-report. "
                         "Audience is design ops leaders and design system managers. "
                         "Should feel like a thoughtful, research-backed newsletter — not marketing fluff."),
    },

    # ── Re-engagement ──
    "reengagement": {
        "campaign_name": "We Miss You",
        "audience": "Users who haven't opened Figma in 90+ days at companies with active Figma seats",
        "goal": "Re-activate 15% of dormant users",
        "key_message": "A lot's happened in 3 months — AI features, Dev Mode, variables support, and 2x faster file loading. Your team is still actively using Figma.",
        "cta_text": "Open Figma",
        "cta_url": "https://figma.com",
        "tone": "reengagement",
        "template_type": "reengagement",
        "additional_context": "Warm and welcoming tone — not guilt-trippy. Use FOMO angle: mention their team is still using Figma actively.",
        "freeform_text": ("Win-back campaign for users who haven't opened Figma in 90+ days. "
                         "We want to show them what they've missed — AI features, Dev Mode, variables support, "
                         "and the new performance improvements (files load 2x faster now). "
                         "Offer a personal touch: mention that their team is still actively using Figma (FOMO angle). "
                         "CTA: 'Open Figma' → https://figma.com. "
                         "Tone should be warm and welcoming, not guilt-trippy. "
                         "Maybe lead with 'A lot's happened in 3 months' and show a quick visual timeline of shipped features. "
                         "Audience is dormant users at companies with active Figma seats."),
    },
    "lapsed_30": {
        "campaign_name": "Checking In",
        "audience": "Users who haven't opened Figma in 30+ days",
        "goal": "Re-engage lapsed users before they hit 90 days dormant",
        "key_message": "We shipped some things you might like: faster file loading, new commenting threads, and dark mode for the desktop app.",
        "cta_text": "Open Figma",
        "cta_url": "https://figma.com",
        "tone": "reengagement",
        "template_type": "reengagement",
        "additional_context": "Softer tone than the 90-day campaign. Keep it light and helpful.",
        "freeform_text": ("Haven't seen you in a bit — just checking in. "
                         "We shipped some things you might like: faster file loading, new commenting threads, and dark mode for the desktop app. "
                         "CTA: Open Figma → https://figma.com. Keep it light and casual, not pushy."),
    },
}


def get_api_key():
    """Get API key from environment if available."""
    return os.environ.get("ANTHROPIC_API_KEY")


def parse_freeform_brief(text: str) -> dict:
    """Use DeepSeek Flash to parse freeform text into structured brief fields."""
    import json as _json
    import re as _re

    system_prompt = """You are a campaign brief parser. Given freeform text describing an email campaign, extract the structured fields below. Infer reasonable defaults where information is missing. Return ONLY valid JSON.

Fields:
- campaign_name: short name for the campaign (string)
- audience: who receives this email (string)
- goal: what success looks like, with metrics if available (string)
- key_message: the one thing they need to know (string)
- cta_text: 2-4 word call to action (string)
- cta_url: full URL for the CTA — always include https:// (e.g. https://figma.com/ai). If only a domain is given, prepend https://
- tone: one of [product_launch, event, feature_update, educational, reengagement]
- template_type: one of [product_launch, event_invite, feature_update, educational, reengagement]
- event_date: date string if this is an event, null otherwise
- additional_context: any extra context that would help generate the email

If the text mentions a specific Figma feature, product, or event, use your knowledge of Figma to fill in reasonable CTA URLs."""

    response_text = _call_deepseek(
        system_prompt=system_prompt,
        user_message=f"Parse this campaign brief:\n\n{text}",
        model=DEEPSEEK_FLASH_MODEL,
        max_tokens=1024,
    )

    # Extract JSON from response
    json_match = _re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, _re.DOTALL)
    if json_match:
        response_text = json_match.group(1)
    return _json.loads(response_text)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Cover page with password gate."""
    error = None
    if request.method == "POST":
        if request.form.get("password") == ACCESS_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        error = "Incorrect password"

    # If already authenticated, skip to app
    if session.get("authenticated"):
        return redirect(url_for("index"))

    return render_template("login.html", error=error)


@app.route("/")
@require_auth
def index():
    """Main page: brief form + results area."""
    return render_template("index.html", samples=SAMPLE_BRIEFS)


@app.route("/api/generate", methods=["POST"])
@require_auth_api
def api_generate():
    """Generate an email from a brief (structured or freeform). Returns JSON with the full result."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    parsed_fields = None

    # Freeform mode: parse first, then generate
    if data.get("freeform_text"):
        if not DEEPSEEK_API_KEY:
            return jsonify({"status": "failed", "errors": ["Freeform parsing requires a DeepSeek API key. Switch to Structured mode or configure DEEPSEEK_API_KEY."], "step": "parsing"})
        try:
            parsed_fields = parse_freeform_brief(data["freeform_text"])
        except Exception as e:
            return jsonify({"status": "failed", "errors": [f"Parsing error: {str(e)}"], "step": "parsing"})

        # Build brief from parsed fields
        try:
            brief = EmailBrief(
                campaign_name=parsed_fields.get("campaign_name", ""),
                audience=parsed_fields.get("audience", ""),
                goal=parsed_fields.get("goal", ""),
                key_message=parsed_fields.get("key_message", ""),
                cta_text=parsed_fields.get("cta_text", ""),
                cta_url=parsed_fields.get("cta_url", ""),
                tone=parsed_fields.get("tone", "educational"),
                template_type=parsed_fields.get("template_type", "educational"),
                additional_context=parsed_fields.get("additional_context", ""),
                event_date=parsed_fields.get("event_date"),
            )
        except Exception as e:
            return jsonify({"status": "failed", "errors": [f"Invalid parsed brief: {str(e)}"], "step": "validation"})
    else:
        # Structured mode: build from form fields
        try:
            brief = EmailBrief(
                campaign_name=data.get("campaign_name", ""),
                audience=data.get("audience", ""),
                goal=data.get("goal", ""),
                key_message=data.get("key_message", ""),
                cta_text=data.get("cta_text", ""),
                cta_url=data.get("cta_url", ""),
                tone=data.get("tone", "educational"),
                template_type=data.get("template_type", "educational"),
                additional_context=data.get("additional_context", ""),
                event_date=data.get("event_date"),
            )
        except Exception as e:
            return jsonify({"error": f"Invalid brief: {str(e)}"}), 400

    # Validate
    errors = brief.validate()
    if errors:
        return jsonify({"status": "failed", "errors": errors, "step": "validation"})

    # Generate
    api_key = get_api_key()
    try:
        email = generate_email(brief, api_key=api_key)
    except Exception as e:
        return jsonify({"status": "failed", "errors": [f"Generation error: {str(e)}"], "step": "generation"})

    # Brand check
    checker = BrandChecker()
    brand_report = checker.check(email.subject_line, email.html_body, email.plain_text)

    # Render preview HTML string
    preview_html = render_preview(email, brand_report)

    # Build response
    violations = []
    for v in brand_report.violations:
        violations.append({"severity": v.severity, "rule": v.rule, "detail": v.detail, "location": v.location})
    for w in brand_report.warnings:
        violations.append({"severity": w.severity, "rule": w.rule, "detail": w.detail, "location": w.location})

    # Try Customer.io sync
    from sync import sync_to_customer_io
    sync_result = sync_to_customer_io(email, brief)

    response = {
        "status": "generated",
        "subject_line": email.subject_line,
        "preview_text": email.preview_text,
        "html_body": email.html_body,
        "plain_text": email.plain_text,
        "template_used": email.template_used,
        "confidence_score": email.confidence_score,
        "brand_passed": brand_report.passed,
        "brand_violations": violations,
        "preview_html": preview_html,
        "provider": get_active_provider(),
        "sync": {
            "success": sync_result.success,
            "provider": sync_result.provider,
            "detail": sync_result.detail,
            "preview_url": sync_result.preview_url,
        },
    }

    # Include parsed fields so the frontend can backfill the structured form
    if parsed_fields:
        response["parsed_fields"] = parsed_fields

    return jsonify(response)


@app.route("/api/samples", methods=["GET"])
@require_auth_api
def api_samples():
    """Return sample briefs for the demo."""
    return jsonify(SAMPLE_BRIEFS)


@app.route("/api/subject-variations", methods=["POST"])
@require_auth_api
def api_subject_variations():
    """Generate subject line variations using DeepSeek Flash (lighter task)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        brief = EmailBrief(
            campaign_name=data.get("campaign_name", ""),
            audience=data.get("audience", ""),
            goal=data.get("goal", ""),
            key_message=data.get("key_message", ""),
            cta_text=data.get("cta_text", ""),
            cta_url=data.get("cta_url", ""),
            tone=data.get("tone", "educational"),
            template_type=data.get("template_type", "educational"),
            additional_context=data.get("additional_context", ""),
            event_date=data.get("event_date"),
        )
    except Exception as e:
        return jsonify({"error": f"Invalid brief: {str(e)}"}), 400

    if not DEEPSEEK_API_KEY:
        return jsonify({"error": "Subject variations require a DeepSeek API key"}), 400

    try:
        variations = generate_subject_variations(brief)
        return jsonify({"status": "ok", "variations": variations, "model": "deepseek-v4-flash"})
    except Exception as e:
        return jsonify({"status": "failed", "errors": [str(e)]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
