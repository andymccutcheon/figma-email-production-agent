"""
Email Generator — LLM-powered email creation.

Uses the prompt from prompts/email-generation.md and context files.
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


@dataclass
class GeneratedEmail:
    subject_line: str
    preview_text: str
    html_body: str
    plain_text: str
    template_used: str
    confidence_score: int  # 1-5

    def to_dict(self) -> dict:
        return asdict(self)


def load_prompt(name: str) -> str:
    """Load a prompt file from the prompts/ directory."""
    prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
    path = os.path.join(prompt_dir, f"{name}.md")
    with open(path) as f:
        return f.read()


def load_context(name: str) -> str:
    """Load a context file from the context/ directory."""
    ctx_dir = os.path.join(os.path.dirname(__file__), "context")
    path = os.path.join(ctx_dir, f"{name}.md")
    with open(path) as f:
        return f.read()


def build_system_prompt(brief: EmailBrief) -> str:
    """Build the full system prompt by combining the email-generation prompt with context files."""
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

Generate the email now. Return ONLY valid JSON -- no other text."""


def _call_deepseek(system_prompt: str, user_message: str, model: str, max_tokens: int = 4096) -> str:
    """Call the DeepSeek API with the given model and return the response text."""
    import json as _json
    from urllib.request import Request, urlopen

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

    resp = urlopen(req, timeout=60)
    data = _json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from an LLM response (handles markdown code blocks)."""
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    return json.loads(text)


def _generate_with_deepseek(brief: EmailBrief) -> GeneratedEmail:
    """Generate a full email using DeepSeek Pro (complex task)."""
    system_prompt = build_system_prompt(brief)
    response_text = _call_deepseek(
        system_prompt=system_prompt,
        user_message="Generate the email based on the brief and system instructions. Return only valid JSON.",
        model=DEEPSEEK_PRO_MODEL,
    )
    data = _extract_json(response_text)
    return GeneratedEmail(**{k: data[k] for k in GeneratedEmail.__dataclass_fields__ if k in data})


def generate_subject_variations(brief: EmailBrief, count: int = 3) -> list[dict]:
    """
    Generate subject line variations using DeepSeek Flash (lighter task).
    Falls back to Pro if Flash key isn't configured separately.
    """
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
        model=DEEPSEEK_FLASH_MODEL,  # Flash for lighter tasks
        max_tokens=1024,
    )
    return _extract_json(response_text)


def generate_email(brief: EmailBrief, api_key: Optional[str] = None) -> GeneratedEmail:
    """
    Generate an email from a brief.

    Routing:
    - DeepSeek Pro (deepseek-v4-pro) → full email generation (complex)
    - DeepSeek Flash (deepseek-v4-flash) → subject line variations (lighter)

    Falls back to Claude or demo mode if no DeepSeek key.
    """
    if DEEPSEEK_API_KEY:
        return _generate_with_deepseek(brief)

    if api_key:
        return _generate_with_claude(brief, api_key)

    return _generate_demo(brief)


def _generate_with_claude(brief: EmailBrief, api_key: str) -> GeneratedEmail:
    """Call the Anthropic API to generate the email."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(brief)

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": "Generate the email based on the brief and system instructions. Return only valid JSON."}]
    )

    # Extract text from response — handle both TextBlock and ThinkingBlock
    response_text = ""
    for block in message.content:
        if hasattr(block, 'text') and block.type != 'thinking':
            response_text = block.text
            break
    if not response_text:
        raise ValueError("No text content in LLM response")

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)

    data = json.loads(response_text)
    return GeneratedEmail(**{k: data[k] for k in GeneratedEmail.__dataclass_fields__ if k in data})


def get_active_provider() -> str:
    """Return which provider is active for display in the UI."""
    if DEEPSEEK_API_KEY:
        return "DeepSeek"
    if ANTHROPIC_API_KEY:
        return "Claude"
    return "demo"


# ── Demo mode (below) — unchanged ──────────────────────────


def _generate_demo(brief: EmailBrief) -> GeneratedEmail:
    """
    Generate a simulated email for demo purposes.
    Produces a realistic, on-brand email that demonstrates the pipeline without API calls.
    """
    template_content = _get_template_content(brief)

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{brief.campaign_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#F5F5F5;font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F5F5F5;">
  <tr>
    <td align="center" style="padding:20px 0;">
      <table width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF;border-radius:8px;overflow:hidden;">

        <!-- View in browser -->
        <tr>
          <td style="padding:16px 24px 0;text-align:center;">
            <a href="https://figma.com" style="color:#666666;font-size:12px;text-decoration:underline;">View in browser</a>
          </td>
        </tr>

        <!-- Logo -->
        <tr>
          <td style="padding:24px;text-align:center;">
            <a href="https://figma.com" style="text-decoration:none;">
              <img src="https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png" alt="Figma" width="40" height="40" style="display:block;margin:0 auto;">
            </a>
          </td>
        </tr>

        {template_content}

        <!-- Footer -->
        <tr>
          <td style="padding:32px 24px;border-top:1px solid #F5F5F5;">
            <p style="font-size:12px;color:#666666;line-height:1.6;text-align:center;margin:0 0 8px;">
              You're receiving this because you're part of the Figma community.
            </p>
            <p style="font-size:12px;color:#666666;line-height:1.6;text-align:center;margin:0 0 8px;">
              <a href="https://figma.com/unsubscribe" style="color:#666666;">Unsubscribe</a> |
              <a href="https://figma.com/preferences" style="color:#666666;">Manage preferences</a>
            </p>
            <p style="font-size:12px;color:#666666;line-height:1.6;text-align:center;margin:0;">
              Figma, Inc. 760 Market St, San Francisco, CA 94102
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""

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


def _get_template_content(brief: EmailBrief) -> str:
    """Generate template-specific HTML content based on the brief's template type."""
    key_message = brief.key_message

    if brief.template_type == "product_launch":
        return f"""<!-- Hero -->
        <tr>
          <td style="padding:0 24px 24px;text-align:center;">
            <h1 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:28px;font-weight:700;color:#000000;margin:0 0 12px;line-height:1.3;">
              {brief.campaign_name}
            </h1>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#666666;line-height:1.6;margin:0 0 24px;max-width:480px;display:inline-block;">
              {key_message}
            </p>
            <a href="{brief.cta_url}" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;font-weight:600;text-decoration:none;padding:14px 32px;border-radius:8px;">
              {brief.cta_text}
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;background-color:#F5F5F5;">
            <h2 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:20px;font-weight:600;color:#000000;margin:0 0 16px;">What's new</h2>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td style="padding:12px 0;"><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;margin:0 0 4px;font-weight:600;">Built for speed</p><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666666;margin:0;">New rendering engine makes every interaction feel instant, even on complex files.</p></td></tr>
              <tr><td style="padding:12px 0;"><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;margin:0 0 4px;font-weight:600;">Collaborate in real time</p><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666666;margin:0;">Multiplayer cursors now show what everyone's working on — no more stepping on toes.</p></td></tr>
              <tr><td style="padding:12px 0;"><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;margin:0 0 4px;font-weight:600;">Design systems that scale</p><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666666;margin:0;">Variables and modes make it easy to build once and deploy everywhere.</p></td></tr>
            </table>
          </td>
        </tr>"""

    elif brief.template_type == "event_invite":
        event_date = brief.event_date or "Coming soon"
        return f"""<!-- Event Hero -->
        <tr>
          <td style="padding:24px;text-align:center;background-color:#0D99FF;">
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:rgba(255,255,255,0.8);margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">You're invited</p>
            <h1 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:28px;font-weight:700;color:#FFFFFF;margin:0 0 12px;line-height:1.3;">{brief.campaign_name}</h1>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:18px;color:rgba(255,255,255,0.9);margin:0 0 8px;">{event_date}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;">
            <h2 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:20px;font-weight:600;color:#000000;margin:0 0 16px;">Why attend</h2>
            <ul style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;line-height:1.8;margin:0 0 24px;padding:0 0 0 20px;">
              <li style="margin-bottom:8px;">Learn how leading teams ship design at scale</li>
              <li style="margin-bottom:8px;">Get hands-on with new Figma features before anyone else</li>
              <li style="margin-bottom:8px;">Connect with designers and builders who share your challenges</li>
            </ul>
            <div style="text-align:center;">
              <a href="{brief.cta_url}" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;font-weight:600;text-decoration:none;padding:14px 32px;border-radius:8px;">{brief.cta_text}</a>
            </div>
          </td>
        </tr>"""

    elif brief.template_type == "feature_update":
        return f"""<!-- Feature Update -->
        <tr>
          <td style="padding:0 24px 24px;text-align:center;">
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#0D99FF;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">New in Figma</p>
            <h1 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:28px;font-weight:700;color:#000000;margin:0 0 12px;line-height:1.3;">{brief.campaign_name}</h1>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#666666;line-height:1.6;margin:0 0 24px;max-width:480px;display:inline-block;">{key_message}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;background-color:#F5F5F5;">
            <h2 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:20px;font-weight:600;color:#000000;margin:0 0 16px;">What changed</h2>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td style="padding:0 0 16px;"><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;margin:0 0 4px;">Faster load times across all files</p><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666666;margin:0;">We rebuilt the rendering engine from scratch. Files open in half the time.</p></td></tr>
              <tr><td style="padding:0 0 16px;"><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;margin:0 0 4px;">New keyboard shortcuts for power users</p><p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666666;margin:0;">Navigate, select, and transform without touching your mouse. Full shortcut guide inside.</p></td></tr>
            </table>
            <div style="text-align:center;padding-top:8px;">
              <a href="{brief.cta_url}" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;font-weight:600;text-decoration:none;padding:14px 32px;border-radius:8px;">{brief.cta_text}</a>
            </div>
          </td>
        </tr>"""

    else:  # educational
        return f"""<!-- Newsletter Header -->
        <tr>
          <td style="padding:0 24px 24px;text-align:center;">
            <h1 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:28px;font-weight:700;color:#000000;margin:0 0 12px;line-height:1.3;">{brief.campaign_name}</h1>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#666666;line-height:1.6;margin:0;max-width:480px;display:inline-block;">{key_message}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;background-color:#F5F5F5;">
            <h2 style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:20px;font-weight:600;color:#000000;margin:0 0 12px;">What we're thinking about</h2>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;line-height:1.6;margin:0 0 16px;">{brief.goal}</p>
            <p style="font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;color:#000000;line-height:1.6;margin:0 0 24px;">The best teams we work with share a common trait: they treat design as a team sport, not a handoff. When engineers, PMs, and designers all work in the same canvas, decisions happen faster and nothing gets lost in translation.</p>
            <div style="text-align:center;">
              <a href="{brief.cta_url}" style="display:inline-block;background-color:#0D99FF;color:#FFFFFF;font-family:'Figma Standard Text','Helvetica Neue',Arial,sans-serif;font-size:16px;font-weight:600;text-decoration:none;padding:14px 32px;border-radius:8px;">{brief.cta_text}</a>
            </div>
          </td>
        </tr>"""


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
