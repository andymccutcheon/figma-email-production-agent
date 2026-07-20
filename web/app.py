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
from generate import generate_email, GeneratedEmail, get_active_provider, generate_subject_variations, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_FLASH_MODEL
from brand_check import BrandChecker, BrandCheckReport
from preview import render_preview

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True,
    APPLICATION_ROOT=os.environ.get("APPLICATION_ROOT", ""),
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
    },
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
    },
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
    },
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
    },
}


def get_api_key():
    """Get API key from environment if available."""
    return os.environ.get("ANTHROPIC_API_KEY")


def parse_freeform_brief(text: str) -> dict:
    """Use DeepSeek Flash to parse freeform text into structured brief fields."""
    import json as _json
    import re as _re
    from urllib.request import Request, urlopen

    system_prompt = """You are a campaign brief parser. Given freeform text describing an email campaign, extract the structured fields below. Infer reasonable defaults where information is missing. Return ONLY valid JSON.

Fields:
- campaign_name: short name for the campaign (string)
- audience: who receives this email (string)
- goal: what success looks like, with metrics if available (string)
- key_message: the one thing they need to know (string)
- cta_text: 2-4 word call to action (string)
- cta_url: URL for the CTA, use figma.com if unclear (string)
- tone: one of [product_launch, event, feature_update, educational, reengagement]
- template_type: one of [product_launch, event_invite, feature_update, educational, reengagement]
- event_date: date string if this is an event, null otherwise
- additional_context: any extra context that would help generate the email

If the text mentions a specific Figma feature, product, or event, use your knowledge of Figma to fill in reasonable CTA URLs."""

    payload = _json.dumps({
        "model": DEEPSEEK_FLASH_MODEL,
        "max_tokens": 1024,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this campaign brief:\n\n{text}"},
        ],
    }, ensure_ascii=False).encode("utf-8")

    req = Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        data=payload,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {DEEPSEEK_API_KEY}")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("User-Agent", "figma-email-agent/1.0")

    resp = urlopen(req, timeout=30)
    data = _json.loads(resp.read().decode("utf-8"))
    response_text = data["choices"][0]["message"]["content"]

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
