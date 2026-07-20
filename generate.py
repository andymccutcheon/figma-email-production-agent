"""
Email Generator — LLM-powered email creation using table-based HTML.

The pipeline is:
  1. LLM (or demo fallback) produces production-ready HTML email markup
  2. Brand checker and preview consume the HTML directly

Primary provider: DeepSeek (OpenAI-compatible API).
Falls back to demo/simulated generation when no API key is available.
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv

from intake import EmailBrief
from email_html import (
    PLACEHOLDER_HERO,
    PLACEHOLDER_ROW,
    body_copy,
    bulleted_resources,
    cta_button,
    footer,
    headline,
    hero_image,
    icon_list_row,
    image_left_row,
    inline_link,
    logo_block,
    newsletter_card_close,
    newsletter_card_open,
    two_column_grid,
    wrap_document,
)

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Provider configuration ─────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_PRO_MODEL = os.environ.get("DEEPSEEK_PRO_MODEL", "deepseek-v4-pro")
DEEPSEEK_FLASH_MODEL = os.environ.get("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Claude fallback
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")


def _normalize_html_body(html: str) -> str:
    """Strip markdown fences from LLM HTML output."""
    html = html.strip()
    html = re.sub(r'^```(?:html|xml)?\s*\n?', '', html)
    html = re.sub(r'\n?```\s*$', '', html)
    return html.strip()


def _lineage_for_template(template_type: str) -> str:
    """Route template types to Whyte lifecycle vs Inter newsletter lineages."""
    if template_type == "feature_update":
        return "inter"
    return "whyte"


@dataclass
class GeneratedEmail:
    subject_line: str
    preview_text: str
    html_body: str       # Production-ready HTML email markup
    plain_text: str
    template_used: str
    confidence_score: int  # 1-5

    def to_dict(self) -> dict:
        return asdict(self)


# ── Prompt Loading ─────────────────────────────────────────

def load_prompt(name: str) -> str:
    prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
    path = os.path.join(prompt_dir, f"{name}.md")
    with open(path) as f:
        return f.read()


def load_context(name: str) -> str:
    ctx_dir = os.path.join(os.path.dirname(__file__), "context")
    path = os.path.join(ctx_dir, f"{name}.md")
    with open(path) as f:
        return f.read()


def build_system_prompt(brief: EmailBrief) -> str:
    """Build the full system prompt for HTML email generation."""
    prompt = load_prompt("email-generation")
    brand = load_context("brand-guidelines")
    voice = load_context("voice-and-tone")
    templates = load_context("email-templates")

    return f"""{prompt}

---

## Brand Guidelines (AUTHORITATIVE -- follow these exactly)
{brand}

---

## Voice & Tone (AUTHORITATIVE -- write in this voice)
{voice}

---

## Available Templates
{templates}

---

## The Brief
Campaign: {brief.campaign_name}
Audience: {brief.audience}
Goal: {brief.goal}
Key Message: {brief.key_message}
CTA: "{brief.cta_text}" -> {brief.cta_url}
Tone: {brief.tone}
Template: {brief.template_type}
Additional Context: {brief.additional_context or 'None'}
{"Event Date: " + brief.event_date if brief.event_date else ""}

Generate the email now. Return ONLY valid JSON — no other text."""


# ── DeepSeek API ───────────────────────────────────────────

def _call_deepseek(system_prompt: str, user_message: str, model: str, max_tokens: int = 4096) -> str:
    """Call the DeepSeek API with the given model and return the response text."""
    import json as _json
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    payload = _json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
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

    try:
        resp = urlopen(req, timeout=60)
        data = _json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        if not content or not content.strip():
            raise ValueError("DeepSeek returned empty content — the model may not support this request or the prompt was rejected")
        return content
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"DeepSeek API error ({e.code}): {body}") from e
    except KeyError:
        raise RuntimeError(f"DeepSeek returned unexpected response structure: {_json.dumps(data, indent=2)[:500]}") from None


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from an LLM response (handles markdown code blocks)."""
    if not text or not text.strip():
        raise ValueError("LLM returned empty response — no content to parse")

    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Surface what the LLM actually returned for debugging
        preview = text[:500] + ('...' if len(text) > 500 else '')
        raise ValueError(f"LLM returned invalid JSON: {e}\nFirst 500 chars of response:\n{preview}") from e


def _generate_with_deepseek(brief: EmailBrief) -> GeneratedEmail:
    """Generate a full email using DeepSeek Pro. LLM outputs HTML directly."""
    system_prompt = build_system_prompt(brief)
    response_text = _call_deepseek(
        system_prompt=system_prompt,
        user_message="Generate the email based on the brief and system instructions. Return only valid JSON.",
        model=DEEPSEEK_PRO_MODEL,
    )
    data = _extract_json(response_text)

    html_body = data.get("html_body", "")
    if html_body:
        data["html_body"] = _normalize_html_body(html_body)

    return GeneratedEmail(**{k: data[k] for k in GeneratedEmail.__dataclass_fields__ if k in data})


def generate_subject_variations(brief: EmailBrief, count: int = 3) -> list[dict]:
    """Generate subject line variations using DeepSeek Flash (lighter task)."""
    subject_prompt = load_prompt("subject-line")
    voice = load_context("voice-and-tone")

    system_prompt = f"""{subject_prompt}

## Voice & Tone
{voice}"""

    user_message = f"""Brief:
Campaign: {brief.campaign_name}
Audience: {brief.audience}
Goal: {brief.goal}
Key Message: {brief.key_message}
Tone: {brief.tone}

Generate {count} subject line variations. Return only valid JSON."""

    response_text = _call_deepseek(
        system_prompt=system_prompt,
        user_message=user_message,
        model=DEEPSEEK_FLASH_MODEL,
        max_tokens=1024,
    )
    return _extract_json(response_text)


# ── Routing ────────────────────────────────────────────────

def generate_email(brief: EmailBrief, api_key: Optional[str] = None) -> GeneratedEmail:
    """Generate an email from a brief. Routes to DeepSeek, Claude, or demo."""
    if DEEPSEEK_API_KEY:
        try:
            return _generate_with_deepseek(brief)
        except Exception as e:
            # Fall through to Claude or demo if DeepSeek fails
            print(f"[generate] DeepSeek failed: {e}")
    if ANTHROPIC_API_KEY:
        return _generate_with_claude(brief, ANTHROPIC_API_KEY)
    if api_key:
        return _generate_with_claude(brief, api_key)
    return _generate_demo(brief)


def _generate_with_claude(brief: EmailBrief, api_key: str) -> GeneratedEmail:
    """Call the Anthropic API to generate the email."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(brief)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the email based on the brief and system instructions. Return only valid JSON."}]
    )

    response_text = ""
    for block in message.content:
        if hasattr(block, 'text') and block.type != 'thinking':
            response_text = block.text
            break
    if not response_text:
        raise ValueError("No text content in LLM response")

    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)

    data = json.loads(response_text)

    html_body = data.get("html_body", "")
    if html_body:
        data["html_body"] = _normalize_html_body(html_body)

    return GeneratedEmail(**{k: data[k] for k in GeneratedEmail.__dataclass_fields__ if k in data})


def get_active_provider() -> str:
    """Return which provider is active for display in the UI."""
    if DEEPSEEK_API_KEY:
        return "DeepSeek"
    if ANTHROPIC_API_KEY:
        return "Claude"
    return "demo"

LAST_USED_PROVIDER = "demo"


# ── Demo Mode (HTML-based) ─────────────────────────────────

def _generate_demo(brief: EmailBrief) -> GeneratedEmail:
    """Generate a simulated email using HTML templates. No API calls."""
    html_body = _build_demo_html(brief)

    subject_line = _generate_subject_line(brief)
    preview_text = _generate_preview_text(brief)
    plain_text = _html_to_plain_text(html_body)

    return GeneratedEmail(
        subject_line=subject_line,
        preview_text=preview_text,
        html_body=html_body,
        plain_text=plain_text,
        template_used=brief.template_type,
        confidence_score=4,
    )


def _build_demo_html(brief: EmailBrief) -> str:
    """Build a complete v4.0 HTML email for demo mode."""
    lineage = _lineage_for_template(brief.template_type)
    preview = _generate_preview_text(brief)
    content = _get_template_html(brief)
    return wrap_document(brief.campaign_name, preview, content, lineage=lineage)


def _demo_rows(brief: EmailBrief, rows: list[tuple[str, str, str, str, str]]) -> str:
    """Build image-left rows from (title, body, link_text, link_url, img_alt) tuples."""
    html = ""
    for title, body, link_text, link_url, img_alt in rows:
        html += image_left_row(
            PLACEHOLDER_ROW, img_alt, title, body, link_text, link_url, brief.cta_url
        )
    return html


def _get_template_html(brief: EmailBrief) -> str:
    """Return v4.0 HTML content matching figma-examples archetypes."""
    url = brief.cta_url

    # ── Product Launch (Untitled-1: Whyte onboarding row layout) ──
    if brief.template_type == "product_launch":
        intro = (
            f"We're excited to share what's new. {inline_link('See it in Figma', url)} "
            f"or explore the highlights below."
        )
        rows = _demo_rows(brief, [
            (
                "AI-assisted design",
                "Generate UI from text prompts, autocomplete repetitive tasks, and let AI handle the tedious layers.",
                "Learn more", url, "AI-assisted design in Figma",
            ),
            (
                "Real-time collaboration",
                "Multiplayer cursors, comments, and version history — no context switching required.",
                "See how it works", url, "Real-time collaboration in Figma",
            ),
            (
                "Design systems that scale",
                "Variables, modes, and component properties let you build once and deploy everywhere.",
                "Explore systems", url, "Design systems in Figma",
            ),
        ])
        return (
            logo_block()
            + hero_image(PLACEHOLDER_HERO, brief.campaign_name, url)
            + headline(brief.campaign_name)
            + body_copy(intro)
            + cta_button(brief.cta_text, url, "purple")
            + rows
            + cta_button(brief.cta_text, url, "purple")
            + footer("whyte")
        )

    # ── Event Invite (Whyte lifecycle + event hero) ──
    if brief.template_type == "event_invite":
        event_date = brief.event_date or "Coming soon"
        return (
            logo_block()
            + hero_image(PLACEHOLDER_HERO, brief.campaign_name, url)
            + headline(brief.campaign_name)
            + body_copy(f"{event_date} · {brief.key_message}")
            + cta_button(brief.cta_text, url, "purple")
            + _demo_rows(brief, [
                (
                    "Learn from the best",
                    "See how top design teams ship at scale — from design systems to AI-assisted workflows.",
                    "View agenda", url, "Event session preview",
                ),
                (
                    "Hands-on workshops",
                    "Small, practical sessions led by the people who built the tools.",
                    "Register now", url, "Workshop preview",
                ),
                (
                    "Connect with peers",
                    "The hallway conversations are as valuable as the keynotes.",
                    "Join the community", url, "Community at Config",
                ),
            ])
            + cta_button(brief.cta_text, url, "purple")
            + footer("whyte")
        )

    # ── Feature Update (Untitled-2: Inter newsletter card) ──
    if brief.template_type == "feature_update":
        card_hero = "https://static.figma.com/uploads/09d331398f2b57bee77b7339209ec2cd4190d6bb"
        return (
            logo_block()
            + newsletter_card_open()
            + hero_image(card_hero, "Release Notes", url)
            + headline(brief.campaign_name, "inter")
            + body_copy(brief.key_message, "inter", "left")
            + two_column_grid(
                "https://static.figma.com/uploads/7cbabd510cbe2f41dc9ca3a027f058d08ea71223",
                "Feature highlight one",
                "Built for speed",
                "Files open in half the time — even complex canvases with thousands of layers.",
                url,
                PLACEHOLDER_ROW,
                "Feature highlight two",
                "Smarter workflows",
                "New shortcuts, improved search, and better layer organization.",
                url,
            )
            + icon_list_row(
                PLACEHOLDER_ROW,
                "Integration icon",
                "And a whole lot more",
                "Deeper integrations with the tools your team already uses.",
            )
            + cta_button(brief.cta_text, url, "black", "inter")
            + newsletter_card_close()
            + footer("inter")
        )

    # ── Re-engagement (Untitled-3: Whyte + outline CTA) ──
    if brief.template_type == "reengagement":
        return (
            logo_block()
            + hero_image(PLACEHOLDER_HERO, "Go to Figma", url)
            + headline("A lot's happened")
            + body_copy(brief.key_message)
            + _demo_rows(brief, [
                (
                    "AI features are live",
                    "Generate UI from text, autocomplete designs, and let AI handle repetitive work.",
                    "Try AI features", url, "Figma AI features",
                ),
                (
                    "Dev Mode keeps getting better",
                    "Annotated specs, code snippets in 8 languages, and a VS Code extension.",
                    "Open Dev Mode", url, "Dev Mode in Figma",
                ),
                (
                    "2x faster file loading",
                    "We rebuilt the rendering engine. Files open in half the time.",
                    "See what's new", url, "Faster file loading",
                ),
            ])
            + cta_button(brief.cta_text or "Go to Figma", url, "outline")
            + footer("whyte")
        )

    # ── Educational (Untitled-4: bulleted resources + outline CTA) ──
    return (
        logo_block()
        + hero_image(PLACEHOLDER_HERO, brief.campaign_name, url)
        + headline(brief.campaign_name)
        + body_copy(brief.key_message)
        + bulleted_resources([
            ("Get started with the basics:", "Learn how", url),
            ("Explore templates:", "Browse the gallery", url),
            ("Join the community:", "Find your people", url),
        ])
        + body_copy(
            "That's all for now :) We'll be back with more tips soon.",
            align="left",
        )
        + cta_button(brief.cta_text or "Go to Figma", url, "outline")
        + footer("whyte")
    )


# ── Subject / Preview helpers ──────────────────────────────

def _generate_subject_line(brief: EmailBrief) -> str:
    campaign = brief.campaign_name
    if brief.tone == "product_launch":
        return f"Introducing {campaign} \u2726 Now in Figma"
    elif brief.tone == "event":
        return f"You're invited: {campaign}"
    elif brief.tone == "feature_update":
        return f"{campaign} \u2014 now faster and smarter"
    else:
        return campaign


def _generate_preview_text(brief: EmailBrief) -> str:
    key = brief.key_message
    if len(key) > 90:
        key = key[:87] + '...'
    return key


def _html_to_plain_text(html: str) -> str:
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'</?(?:div|p|tr|table|h[1-6]|ul|ol|li|br)[^>]*>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()
