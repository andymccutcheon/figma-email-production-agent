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


# ── HTML Email Building Blocks ───────────────────────────────

FONT_STACK = "'Helvetica Neue', Arial, sans-serif"


def _normalize_html_body(html: str) -> str:
    """Strip markdown fences from LLM HTML output."""
    html = html.strip()
    html = re.sub(r'^```(?:html|xml)?\s*\n?', '', html)
    html = re.sub(r'\n?```\s*$', '', html)
    return html.strip()


def _html_section(bg: str, padding: str, inner: str) -> str:
    return f"""<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:{bg};width:100%;max-width:600px;margin:0 auto;">
<tr><td style="padding:{padding};">
{inner}
</td></tr></table>"""


def _html_text(
    content: str,
    *,
    font_size: str = "16px",
    font_weight: str = "400",
    color: str = "#1E1E1E",
    align: str = "left",
    padding: str = "0 25px",
    padding_bottom: str = "12px",
    line_height: str = "1.6",
    letter_spacing: Optional[str] = None,
    text_transform: Optional[str] = None,
) -> str:
    extra = ""
    if letter_spacing:
        extra += f"letter-spacing:{letter_spacing};"
    if text_transform:
        extra += f"text-transform:{text_transform};"
    return (
        f'<div style="font-family:{FONT_STACK};font-size:{font_size};font-weight:{font_weight};'
        f'color:{color};text-align:{align};padding:{padding};padding-bottom:{padding_bottom};'
        f'line-height:{line_height};{extra}">{content}</div>'
    )


def _html_button(text: str, url: str, align: str = "center") -> str:
    return (
        f'<div style="text-align:{align};padding:10px 25px;">'
        f'<a href="{url}" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;'
        f'font-family:{FONT_STACK};font-size:16px;font-weight:600;border-radius:8px;'
        f'padding:14px 32px;text-decoration:none;">{text}</a></div>'
    )


def _html_footer() -> str:
    return _html_section(
        "#FFFFFF",
        "30px 30px",
        _html_text(
            "You're receiving this because you're part of the Figma community.",
            font_size="12px",
            color="#666666",
            align="center",
            padding_bottom="8px",
            line_height="1.5",
        )
        + _html_text(
            '<a href="https://figma.com/unsubscribe" style="color:#666666;text-decoration:none;">Unsubscribe</a>'
            ' · <a href="https://figma.com/preferences" style="color:#666666;text-decoration:none;">Email Preferences</a>',
            font_size="12px",
            color="#666666",
            align="center",
            padding_bottom="12px",
            line_height="1.5",
        )
        + _html_text(
            "Figma, Inc. 760 Market St, San Francisco, CA 94102",
            font_size="12px",
            color="#666666",
            align="center",
            padding_bottom="0",
            line_height="1.5",
        ),
    )


# ── Logo URL ───────────────────────────────────────────────

LOGO_URL = "https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png"


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
    """Build a complete HTML email document for demo mode."""
    template_content = _get_template_html(brief)
    logo_block = (
        f'<div style="text-align:center;padding:10px 0;">'
        f'<img src="{LOGO_URL}" alt="Figma" width="40" '
        f'style="width:40px;max-width:100%;height:auto;border:0;" /></div>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{brief.campaign_name}</title>
<style>
  body {{ margin:0; padding:0; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  img {{ border:0; height:auto; line-height:100%; outline:none; text-decoration:none; max-width:100%; }}
</style>
</head>
<body style="word-spacing:normal;background-color:#F5F5F5;margin:0;padding:0;">
<div style="background-color:#F5F5F5;margin:0 auto;max-width:600px;">
  {_html_section("#F5F5F5", "12px 30px 0", _html_text('<a href="https://figma.com" style="color:#666666;text-decoration:none;">View in browser</a>', font_size="12px", color="#666666", align="center", padding_bottom="0"))}
  {_html_section("#F5F5F5", "24px 30px 8px", logo_block)}
  {template_content}
  {_html_footer()}
</div>
</body>
</html>"""


def _get_template_html(brief: EmailBrief) -> str:
    """Return HTML content for the specific template type, following v3.0 design system."""

    # ── Product Launch ──
    if brief.template_type == "product_launch":
        return (
            _html_section(
                "#FFFFFF",
                "40px 30px",
                _html_text(brief.campaign_name, font_size="28px", font_weight="700", color="#000000", align="center", padding_bottom="12px")
                + _html_text(brief.key_message, align="center", padding_bottom="24px")
                + _html_button(brief.cta_text, brief.cta_url),
            )
            + _html_section(
                "#FAFAFA",
                "30px 30px",
                _html_text("Designed for the way you work", font_size="20px", font_weight="600", color="#000000", padding_bottom="20px")
                + _html_text("AI-assisted design", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Generate UI from text prompts, autocomplete repetitive tasks, and let AI handle the tedious layers so you can focus on creative decisions.",
                    padding_bottom="20px",
                )
                + _html_text("Real-time collaboration", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Multiplayer cursors show what everyone's working on. Comments, audio calls, and version history are built in — no context switching.",
                    padding_bottom="20px",
                )
                + _html_text("Design systems that scale", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Variables, modes, and component properties let you build once and deploy everywhere. Ship consistent experiences across every surface.",
                    padding_bottom="0",
                ),
            )
            + _html_section("#FFFFFF", "20px 30px", _html_button(brief.cta_text, brief.cta_url))
        )

    # ── Event Invite ──
    if brief.template_type == "event_invite":
        event_date = brief.event_date or "Coming soon"
        return (
            _html_section(
                "#0D99FF",
                "50px 30px",
                _html_text(
                    "You're invited",
                    font_size="13px",
                    font_weight="600",
                    color="rgba(255,255,255,0.7)",
                    align="center",
                    padding_bottom="16px",
                    letter_spacing="0.08em",
                    text_transform="uppercase",
                )
                + _html_text(brief.campaign_name, font_size="28px", font_weight="700", color="#FFFFFF", align="center", padding_bottom="12px")
                + _html_text(event_date, font_size="18px", color="rgba(255,255,255,0.9)", align="center", padding_bottom="0"),
            )
            + _html_section(
                "#FFFFFF",
                "30px 30px",
                _html_text("Why attend", font_size="20px", font_weight="600", color="#000000", padding_bottom="20px")
                + _html_text(
                    "Learn how the best design teams ship at scale — from design systems that serve hundreds of designers to AI-assisted workflows that cut production time in half.",
                    padding_bottom="12px",
                )
                + _html_text(
                    "Get hands-on with new Figma features before anyone else. Our workshops are small, practical, and led by the people who built the tools.",
                    padding_bottom="12px",
                )
                + _html_text(
                    "Connect with designers and builders who share your challenges. The hallway conversations are as valuable as the keynotes.",
                    padding_bottom="24px",
                )
                + _html_button(brief.cta_text, brief.cta_url),
            )
            + _html_section("#FFFFFF", "20px 30px", _html_button(brief.cta_text, brief.cta_url))
        )

    # ── Feature Update ──
    if brief.template_type == "feature_update":
        return (
            _html_section(
                "#FFFFFF",
                "40px 30px",
                _html_text(
                    "New in Figma",
                    font_size="13px",
                    font_weight="600",
                    color="#0D99FF",
                    align="center",
                    padding_bottom="16px",
                    letter_spacing="0.06em",
                    text_transform="uppercase",
                )
                + _html_text(brief.campaign_name, font_size="28px", font_weight="700", color="#000000", align="center", padding_bottom="12px")
                + _html_text(brief.key_message, align="center", padding_bottom="24px")
                + _html_button(brief.cta_text, brief.cta_url),
            )
            + _html_section(
                "#FAFAFA",
                "30px 30px",
                _html_text("What changed", font_size="20px", font_weight="600", color="#000000", padding_bottom="20px")
                + _html_text("Built for speed", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "We rebuilt the rendering engine from scratch. Files open in half the time, and every interaction feels instant — even on complex canvases with thousands of layers.",
                    padding_bottom="20px",
                )
                + _html_text("Smarter workflows", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "New keyboard shortcuts, improved search, and better layer organization let you spend less time navigating and more time designing.",
                    padding_bottom="20px",
                )
                + _html_text("Plays well with others", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Deeper integrations with the tools your team already uses. One-click exports, real-time embeds, and API access for custom workflows.",
                    padding_bottom="0",
                ),
            )
            + _html_section("#FFFFFF", "20px 30px", _html_button(brief.cta_text, brief.cta_url))
        )

    # ── Re-engagement ──
    if brief.template_type == "reengagement":
        return (
            _html_section(
                "#FFFFFF",
                "40px 30px",
                _html_text("A lot's happened", font_size="28px", font_weight="700", color="#000000", align="center", padding_bottom="12px")
                + _html_text(brief.key_message, align="center", padding_bottom="24px")
                + _html_button(brief.cta_text, brief.cta_url),
            )
            + _html_section(
                "#FAFAFA",
                "30px 30px",
                _html_text("What you've missed", font_size="20px", font_weight="600", color="#000000", padding_bottom="20px")
                + _html_text("AI features are live", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Generate UI from text, autocomplete designs, and let AI handle the repetitive work. Thousands of teams are already using it daily.",
                    padding_bottom="20px",
                )
                + _html_text("Dev Mode keeps getting better", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "Annotated specs, automatic code snippets in 8 languages, and a VS Code extension that syncs design changes in real time.",
                    padding_bottom="20px",
                )
                + _html_text("2x faster file loading", font_weight="600", color="#000000", padding_bottom="6px")
                + _html_text(
                    "We rebuilt the rendering engine. Files open in half the time — even the big ones with thousands of layers.",
                    padding_bottom="0",
                ),
            )
            + _html_section("#FFFFFF", "20px 30px", _html_button(brief.cta_text, brief.cta_url))
        )

    # ── Educational / Newsletter ──
    return (
        _html_section(
            "#FFFFFF",
            "40px 30px",
            _html_text(brief.campaign_name, font_size="28px", font_weight="700", color="#000000", align="center", padding_bottom="12px")
            + _html_text(brief.key_message, align="center", padding_bottom="24px")
            + _html_button(brief.cta_text, brief.cta_url),
        )
        + _html_section(
            "#FAFAFA",
            "30px 30px",
            _html_text("What we're learning", font_size="20px", font_weight="600", color="#000000", padding_bottom="20px")
            + _html_text(brief.goal, padding_bottom="16px")
            + _html_text(
                "The best teams we work with share a common trait: they treat design as a team sport, not a handoff. When engineers, PMs, and designers all work in the same canvas, decisions happen faster and nothing gets lost in translation. The tools are the enabler — the culture is what makes it stick.",
                padding_bottom="24px",
            )
            + _html_button(brief.cta_text, brief.cta_url),
        )
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
