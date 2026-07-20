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
import xml.etree.ElementTree as ET
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
    """Compile MJML XML to production-ready HTML.

    Tries local MJML binary first, then npx, then falls back to a basic
    Python-based converter that produces renderable (but not Outlook-optimized)
    HTML for preview purposes.
    """
    # Strip any markdown code fences the LLM may have wrapped the MJML in
    mjml = mjml.strip()
    mjml = re.sub(r'^```(?:mjml|xml|html)?\s*\n?', '', mjml)
    mjml = re.sub(r'\n?```\s*$', '', mjml)
    mjml = mjml.strip()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.mjml', delete=False, encoding='utf-8') as f:
        f.write(mjml)
        mjml_path = f.name

    compiled = None

    # Try 1: local node_modules/.bin/mjml
    try:
        local_mjml = os.path.join(os.path.dirname(__file__) if '__file__' in dir() else '.', 'node_modules', '.bin', 'mjml')
        result = subprocess.run(
            [local_mjml, mjml_path, "--config.minify=true", "--config.validationLevel=soft"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            compiled = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try 2: npx mjml (download on-the-fly)
    if compiled is None:
        try:
            result = subprocess.run(
                ["npx", "--yes", "mjml", mjml_path, "--config.minify=true", "--config.validationLevel=soft"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                compiled = result.stdout
            elif result.stdout.strip():
                compiled = result.stdout  # Partial output
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Try 3: Python-based fallback (basic conversion, no Outlook VML)
    if compiled is None:
        print("[MJML] npx/mjml unavailable — using Python fallback converter")
        compiled = _mjml_to_html_python(mjml)

    try:
        os.unlink(mjml_path)
    except OSError:
        pass

    return compiled


def _mjml_to_html_python(mjml: str) -> str:
    """Basic Python-based MJML-to-HTML converter for preview fallback.

    Does NOT produce Outlook VML or responsive media queries — it's meant
    to produce renderable HTML for the browser preview when npx mjml is
    unavailable (e.g. on Vercel serverless where npm packages can't be
    downloaded at runtime).
    """
    # MJML uses namespaced tags, strip the namespace for easier parsing
    cleaned = re.sub(r'xmlns="[^"]*"', '', mjml)
    cleaned = re.sub(r'<mjml[^>]*>', '<mjml>', cleaned, count=1)
    cleaned = re.sub(r'</mjml>', '</mjml>', cleaned, count=1)

    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as e:
        # If XML parsing fails, wrap raw MJML in a basic HTML doc
        escaped = mjml.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Email Preview</title></head>
<body style="font-family:Helvetica,Arial,sans-serif;padding:40px;background:#f5f5f5;color:#333;">
<h3>⚠ MJML compilation unavailable</h3>
<p>The email was generated as MJML but could not be compiled to HTML in this environment. Rendering raw source below.</p>
<pre style="background:#fff;padding:20px;border-radius:8px;overflow:auto;font-size:13px;line-height:1.5;">{escaped}</pre>
</body></html>"""

    # Extract head elements
    title = ""
    extra_styles = ""

    for child in root:
        if child.tag == 'mj-head':
            for el in child:
                if el.tag == 'mj-title':
                    title = (el.text or '').strip()
                elif el.tag == 'mj-style':
                    extra_styles += (el.text or '')
                # mj-attributes are applied per-element, handled during conversion
        elif child.tag == 'mj-body':
            body_content = _convert_mj_body(child)
        else:
            # Direct children of <mjml> that aren't <mj-head> or <mj-body>
            pass

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title or 'Email'}</title>
<style>
  body {{ margin:0; padding:0; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  img {{ border:0; height:auto; line-height:100%; outline:none; text-decoration:none; max-width:100%; }}
  {extra_styles}
</style>
</head>
<body style="word-spacing:normal;background-color:#F5F5F5;">
{body_content}
</body>
</html>"""


def _convert_mj_body(body_el) -> str:
    """Convert <mj-body> and its children to HTML table structure."""
    bg = body_el.get('background-color', '#F5F5F5')

    rows = []
    for child in body_el:
        if child.tag == 'mj-section':
            rows.append(_convert_mj_section(child))
        elif child.tag == 'mj-wrapper':
            for sub in child:
                if sub.tag == 'mj-section':
                    rows.append(_convert_mj_section(sub))

    inner = '\n'.join(rows)
    return f'<div style="background-color:{bg};margin:0 auto;max-width:600px;">\n{inner}\n</div>'


def _convert_mj_section(el) -> str:
    """Convert <mj-section> to a table row."""
    bg = el.get('background-color', '#FFFFFF')
    padding = el.get('padding', '20px 0')

    cols = []
    for child in el:
        if child.tag == 'mj-column':
            cols.append(_convert_mj_column(child))

    cols_html = '\n'.join(cols)
    return f"""<table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background-color:{bg};width:100%;">
<tr><td style="padding:{padding};">
{cols_html}
</td></tr></table>"""


def _convert_mj_column(el) -> str:
    """Convert <mj-column> to a table cell with content."""
    width = el.get('width', '100%')
    padding = el.get('padding', '0')

    inner = []
    for child in el:
        converted = _convert_element(child)
        if converted:
            inner.append(converted)

    inner_html = '\n'.join(inner)
    return f"""<div style="display:inline-block;vertical-align:top;width:{width};padding:{padding};">
{inner_html}
</div>"""


# Map MJML attribute names to inline CSS properties
_STYLE_MAP = {
    'color': 'color',
    'font-size': 'font-size',
    'font-weight': 'font-weight',
    'font-family': 'font-family',
    'line-height': 'line-height',
    'text-align': 'text-align',
    'align': 'text-align',
    'background-color': 'background-color',
    'padding': 'padding',
    'padding-top': 'padding-top',
    'padding-bottom': 'padding-bottom',
    'padding-left': 'padding-left',
    'padding-right': 'padding-right',
    'border-radius': 'border-radius',
    'width': 'width',
    'height': 'height',
    'text-decoration': 'text-decoration',
}

_COLOR_ATTRS = {'color', 'background-color'}


def _mj_style(el, defaults=None) -> str:
    """Build an inline style string from MJML element attributes."""
    styles = dict(defaults or {})
    for attr, val in el.attrib.items():
        css_prop = _STYLE_MAP.get(attr)
        if css_prop:
            styles[css_prop] = val
    return ';'.join(f'{k}:{v}' for k, v in styles.items())


def _convert_element(el) -> str:
    """Convert a single MJML element to its HTML equivalent."""
    tag = el.tag

    if tag == 'mj-text':
        style = _mj_style(el, {'font-size': '16px', 'color': '#1E1E1E', 'line-height': '1.6'})
        text = el.text or ''
        # Preserve inner HTML (links, bold, etc.) by converting children
        inner = text
        for child in el:
            inner += ET.tostring(child, encoding='unicode')
        if el.tail:
            inner += el.tail
        return f'<div style="{style}">{inner.strip()}</div>'

    elif tag == 'mj-button':
        href = el.get('href', '#')
        bg = el.get('background-color', '#0D99FF')
        color = el.get('color', '#FFFFFF')
        fs = el.get('font-size', '16px')
        fw = el.get('font-weight', '600')
        br = el.get('border-radius', '8px')
        padding = el.get('padding', '14px 32px')
        text = (el.text or '').strip()
        align = el.get('align', 'center')
        return f"""<div style="text-align:{align};padding:10px 0;">
<a href="{href}" style="display:inline-block;background:{bg};color:{color};font-size:{fs};font-weight:{fw};border-radius:{br};padding:{padding};text-decoration:none;font-family:Helvetica,Arial,sans-serif;">{text}</a>
</div>"""

    elif tag == 'mj-image':
        src = el.get('src', '')
        alt = el.get('alt', '')
        width = el.get('width', '100%')
        align = el.get('align', 'center')
        return f'<div style="text-align:{align};padding:10px 0;"><img src="{src}" alt="{alt}" style="width:{width};max-width:100%;height:auto;border:0;" /></div>'

    elif tag == 'mj-divider':
        border_color = el.get('border-color', '#E5E5E5')
        border_width = el.get('border-width', '1px')
        padding = el.get('padding', '10px 25px')
        return f'<div style="padding:{padding};"><hr style="border:none;border-top:{border_width} solid {border_color};" /></div>'

    elif tag == 'mj-spacer':
        height = el.get('height', '20px')
        return f'<div style="height:{height};"></div>'

    elif tag == 'mj-social':
        return '<div><!-- social icons placeholder --></div>'

    elif tag == 'mj-navbar':
        return '<div><!-- navbar placeholder --></div>'

    elif tag == 'mj-raw':
        return el.text or ''

    # Catch-all: return text content
    text = el.text or ''
    for child in el:
        text += ET.tostring(child, encoding='unicode')
    return f'<div>{text.strip()}</div>'


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
