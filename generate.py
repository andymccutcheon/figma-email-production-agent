"""
Email Generator — LLM-powered email creation using MJML templates.

MJML is compiled to production-ready HTML with cross-client compatibility
(Outlook, Gmail, Apple Mail, mobile). The pipeline is:
  1. LLM (or demo fallback) produces MJML XML
  2. compile_mjml() converts to HTML via npx mjml
  3. Brand checker and preview consume the compiled HTML

Primary provider: DeepSeek (OpenAI-compatible API).
Falls back to demo/simulated generation when no API key is available.
"""

import json
import os
import re
import subprocess
import tempfile
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


# ── MJML Compilation ───────────────────────────────────────

def compile_mjml(mjml: str) -> str:
    """Compile MJML XML to production-ready HTML via npx mjml.

    Uses --config.minify=true to stay under Gmail's 102KB clip limit
    and --config.validationLevel=soft to handle minor LLM output quirks.
    """
    # Strip any markdown code fences the LLM may have wrapped the MJML in
    mjml = mjml.strip()
    mjml = re.sub(r'^```(?:mjml|xml|html)?\s*\n?', '', mjml)
    mjml = re.sub(r'\n?```\s*$', '', mjml)
    mjml = mjml.strip()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.mjml', delete=False, encoding='utf-8') as f:
        f.write(mjml)
        mjml_path = f.name

    try:
        result = subprocess.run(
            [
                "npx", "mjml", mjml_path,
                "--config.minify=true",
                "--config.validationLevel=soft",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(__file__),
        )

        if result.returncode != 0:
            # If MJML compilation fails, return the raw MJML as a fallback
            err = result.stderr[:500]
            print(f"[MJML] Compilation warning (using raw output): {err}")
            # Try to extract any HTML from the output anyway
            if result.stdout.strip():
                return result.stdout
            raise RuntimeError(f"MJML compilation failed: {err}")

        return result.stdout

    except FileNotFoundError:
        print("[MJML] npx not found — MJML compilation skipped, returning raw MJML")
        return mjml
    except subprocess.TimeoutExpired:
        print("[MJML] Compilation timed out — returning raw MJML")
        return mjml
    finally:
        try:
            os.unlink(mjml_path)
        except OSError:
            pass


# ── Logo URL ───────────────────────────────────────────────

LOGO_URL = "https://userimg-assets.customeriomail.com/images/client-env-226115/01KXY0PTW2FWKDYZ4377K8BM3G.png"


@dataclass
class GeneratedEmail:
    subject_line: str
    preview_text: str
    html_body: str       # Compiled HTML (from MJML)
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
    """Build the full system prompt for MJML email generation."""
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
    """Generate a full email using DeepSeek Pro. LLM outputs MJML, we compile to HTML."""
    system_prompt = build_system_prompt(brief)
    response_text = _call_deepseek(
        system_prompt=system_prompt,
        user_message="Generate the email based on the brief and system instructions. Return only valid JSON.",
        model=DEEPSEEK_PRO_MODEL,
    )
    data = _extract_json(response_text)

    # The LLM outputs MJML in html_body — compile it to real HTML
    # Strip markdown fences before checking
    mjml_source = data.get("html_body", data.get("mjml_body", ""))
    if mjml_source:
        mjml_source = mjml_source.strip()
        mjml_source = re.sub(r'^```(?:mjml|xml|html)?\s*\n?', '', mjml_source)
        mjml_source = re.sub(r'\n?```\s*$', '', mjml_source)
    if mjml_source and "<mjml" in mjml_source:
        data["html_body"] = compile_mjml(mjml_source)

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

    # Compile MJML to HTML if present
    mjml_source = data.get("html_body", data.get("mjml_body", ""))
    if mjml_source:
        mjml_source = mjml_source.strip()
        mjml_source = re.sub(r'^```(?:mjml|xml|html)?\s*\n?', '', mjml_source)
        mjml_source = re.sub(r'\n?```\s*$', '', mjml_source)
    if mjml_source and "<mjml" in mjml_source:
        data["html_body"] = compile_mjml(mjml_source)

    return GeneratedEmail(**{k: data[k] for k in GeneratedEmail.__dataclass_fields__ if k in data})


def get_active_provider() -> str:
    """Return which provider is active for display in the UI."""
    if DEEPSEEK_API_KEY:
        return "DeepSeek"
    if ANTHROPIC_API_KEY:
        return "Claude"
    return "demo"

LAST_USED_PROVIDER = "demo"


# ── Demo Mode (MJML-based) ─────────────────────────────────

def _generate_demo(brief: EmailBrief) -> GeneratedEmail:
    """Generate a simulated email using MJML templates. No API calls."""
    mjml = _build_demo_mjml(brief)
    html_body = compile_mjml(mjml)

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


def _build_demo_mjml(brief: EmailBrief) -> str:
    """Build a complete MJML document for demo mode."""
    template_content = _get_template_mjml(brief)

    return f"""<mjml>
  <mj-head>
    <mj-title>{brief.campaign_name}</mj-title>
    <mj-font name="Figma Standard Text" href="https://fonts.cdnfonts.com/css/helvetica-neue-9" />
    <mj-attributes>
      <mj-all font-family="'Helvetica Neue', Arial, sans-serif" />
      <mj-text font-size="16px" color="#1E1E1E" line-height="1.6" />
      <mj-button background-color="#0D99FF" color="#FFFFFF" font-weight="600" border-radius="8px" padding="14px 32px" font-size="16px" />
    </mj-attributes>
    <mj-style inline="inline">
      .view-in-browser {{ color: #666666; font-size: 12px; }}
      .footer-text {{ color: #666666; font-size: 12px; }}
    </mj-style>
  </mj-head>
  <mj-body background-color="#F5F5F5">
    <!-- View in browser -->
    <mj-section padding="16px 24px 0">
      <mj-column>
        <mj-text align="center" font-size="12px" color="#666666">
          <a href="https://figma.com" style="color:#666666;">View in browser</a>
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Logo -->
    <mj-section padding="24px">
      <mj-column>
        <mj-image src="{LOGO_URL}" alt="Figma" width="40px" align="center" />
      </mj-column>
    </mj-section>

    {template_content}

    <!-- Footer -->
    <mj-section padding="32px 24px" border-top="1px solid #F5F5F5">
      <mj-column>
        <mj-text align="center" font-size="12px" color="#666666" line-height="1.6">
          You're receiving this because you're part of the Figma community.
        </mj-text>
        <mj-text align="center" font-size="12px" color="#666666" line-height="1.6">
          <a href="https://figma.com/unsubscribe" style="color:#666666;">Unsubscribe</a> |
          <a href="https://figma.com/preferences" style="color:#666666;">Manage preferences</a>
        </mj-text>
        <mj-text align="center" font-size="12px" color="#666666" line-height="1.6">
          Figma, Inc. 760 Market St, San Francisco, CA 94102
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""


def _get_template_mjml(brief: EmailBrief) -> str:
    """Return MJML content for the specific template type."""
    key_message = brief.key_message

    if brief.template_type == "product_launch":
        return f"""<!-- Hero -->
    <mj-section padding="0 24px 24px">
      <mj-column>
        <mj-text align="center" font-size="28px" font-weight="700" color="#000000" padding="0 0 12px">
          {brief.campaign_name}
        </mj-text>
        <mj-text align="center" font-size="16px" color="#666666" padding="0 0 24px" css-class="hero-description">
          {key_message}
        </mj-text>
        <mj-button href="{brief.cta_url}" align="center">
          {brief.cta_text}
        </mj-button>
      </mj-column>
    </mj-section>

    <!-- Features -->
    <mj-section padding="24px" background-color="#F5F5F5">
      <mj-column>
        <mj-text font-size="20px" font-weight="600" color="#000000" padding="0 0 16px">
          What's new
        </mj-text>
        <mj-text font-size="16px" font-weight="600" color="#000000" padding="0 0 4px">
          Built for speed
        </mj-text>
        <mj-text font-size="14px" color="#666666" padding="0 0 16px">
          New rendering engine makes every interaction feel instant, even on complex files.
        </mj-text>
        <mj-text font-size="16px" font-weight="600" color="#000000" padding="0 0 4px">
          Collaborate in real time
        </mj-text>
        <mj-text font-size="14px" color="#666666" padding="0 0 16px">
          Multiplayer cursors now show what everyone's working on — no more stepping on toes.
        </mj-text>
        <mj-text font-size="16px" font-weight="600" color="#000000" padding="0 0 4px">
          Design systems that scale
        </mj-text>
        <mj-text font-size="14px" color="#666666" padding="0 0 8px">
          Variables and modes make it easy to build once and deploy everywhere.
        </mj-text>
      </mj-column>
    </mj-section>"""

    elif brief.template_type == "event_invite":
        event_date = brief.event_date or "Coming soon"
        return f"""<!-- Event Hero -->
    <mj-section padding="24px" background-color="#0D99FF">
      <mj-column>
        <mj-text align="center" font-size="14px" color="rgba(255,255,255,0.8)" text-transform="uppercase" padding="0 0 8px">
          You're invited
        </mj-text>
        <mj-text align="center" font-size="28px" font-weight="700" color="#FFFFFF" padding="0 0 12px">
          {brief.campaign_name}
        </mj-text>
        <mj-text align="center" font-size="18px" color="rgba(255,255,255,0.9)" padding="0 0 8px">
          {event_date}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Why attend -->
    <mj-section padding="24px">
      <mj-column>
        <mj-text font-size="20px" font-weight="600" color="#000000" padding="0 0 16px">
          Why attend
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 8px">
          • Learn how leading teams ship design at scale
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 8px">
          • Get hands-on with new Figma features before anyone else
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 24px">
          • Connect with designers and builders who share your challenges
        </mj-text>
        <mj-button href="{brief.cta_url}" align="center">
          {brief.cta_text}
        </mj-button>
      </mj-column>
    </mj-section>"""

    elif brief.template_type == "feature_update":
        return f"""<!-- Feature Update -->
    <mj-section padding="0 24px 24px">
      <mj-column>
        <mj-text align="center" font-size="14px" color="#0D99FF" text-transform="uppercase" padding="0 0 8px">
          New in Figma
        </mj-text>
        <mj-text align="center" font-size="28px" font-weight="700" color="#000000" padding="0 0 12px">
          {brief.campaign_name}
        </mj-text>
        <mj-text align="center" font-size="16px" color="#666666" padding="0 0 24px" css-class="update-description">
          {key_message}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- What changed -->
    <mj-section padding="24px" background-color="#F5F5F5">
      <mj-column>
        <mj-text font-size="20px" font-weight="600" color="#000000" padding="0 0 16px">
          What changed
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 4px">
          Faster load times across all files
        </mj-text>
        <mj-text font-size="14px" color="#666666" padding="0 0 16px">
          We rebuilt the rendering engine from scratch. Files open in half the time.
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 4px">
          New keyboard shortcuts for power users
        </mj-text>
        <mj-text font-size="14px" color="#666666" padding="0 0 16px">
          Navigate, select, and transform without touching your mouse. Full shortcut guide inside.
        </mj-text>
        <mj-button href="{brief.cta_url}" align="center">
          {brief.cta_text}
        </mj-button>
      </mj-column>
    </mj-section>"""

    else:  # educational
        return f"""<!-- Newsletter Header -->
    <mj-section padding="0 24px 24px">
      <mj-column>
        <mj-text align="center" font-size="28px" font-weight="700" color="#000000" padding="0 0 12px">
          {brief.campaign_name}
        </mj-text>
        <mj-text align="center" font-size="16px" color="#666666" padding="0 0 24px" css-class="newsletter-description">
          {key_message}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Article -->
    <mj-section padding="24px" background-color="#F5F5F5">
      <mj-column>
        <mj-text font-size="20px" font-weight="600" color="#000000" padding="0 0 12px">
          What we're thinking about
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 16px">
          {brief.goal}
        </mj-text>
        <mj-text font-size="16px" color="#000000" padding="0 0 24px">
          The best teams we work with share a common trait: they treat design as a team sport, not a handoff. When engineers, PMs, and designers all work in the same canvas, decisions happen faster and nothing gets lost in translation.
        </mj-text>
        <mj-button href="{brief.cta_url}" align="center">
          {brief.cta_text}
        </mj-button>
      </mj-column>
    </mj-section>"""


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
