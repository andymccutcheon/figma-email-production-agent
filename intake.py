"""
Brief Intake — Parse and validate the marketer's email brief.

Deterministic module. No LLM calls.
Validates required fields, data types, and business rules before
anything touches the model. Fails fast with specific errors.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


def normalize_url(url: str) -> str:
    """Ensure a URL has a scheme. Bare domains get https:// prepended."""
    url = (url or "").strip()
    if not url:
        return url
    if re.match(r"^https?://", url, re.IGNORECASE):
        return url
    # help.figma.com/variables, figma.com/ai, config.figma.com/2026, etc.
    if re.match(r"^[\w.-]+\.\w+(/.*)?$", url):
        return f"https://{url}"
    return url


@dataclass
class EmailBrief:
    campaign_name: str
    audience: str
    goal: str
    key_message: str
    cta_text: str
    cta_url: str
    tone: str  # product_launch, event, educational, feature_update, reengagement
    template_type: str  # product_launch, event_invite, educational, feature_update, reengagement
    additional_context: str = ""
    sender_name: str = "Figma"
    sender_email: str = "hello@figma.com"

    # Optional fields
    hero_image_url: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    target_segment: Optional[str] = None

    def __post_init__(self) -> None:
        self.cta_url = normalize_url(self.cta_url)
        if self.hero_image_url:
            self.hero_image_url = normalize_url(self.hero_image_url)

    def validate(self) -> list[str]:
        """Run all validations. Returns list of error messages (empty = valid)."""
        errors = []

        # Required fields
        if not self.campaign_name or len(self.campaign_name.strip()) < 3:
            errors.append("campaign_name is required (min 3 characters)")

        if not self.audience or len(self.audience.strip()) < 3:
            errors.append("audience is required (min 3 characters)")

        if not self.goal or len(self.goal.strip()) < 10:
            errors.append("goal is required (min 10 characters — describe what success looks like)")

        if not self.key_message or len(self.key_message.strip()) < 10:
            errors.append("key_message is required (min 10 characters)")

        # CTA validation
        if not self.cta_text:
            errors.append("cta_text is required")
        elif len(self.cta_text.split()) > 4:
            errors.append(f"cta_text must be 2-4 words, got {len(self.cta_text.split())}: '{self.cta_text}'")

        if not self.cta_url:
            errors.append("cta_url is required")
        elif not re.match(r"^https?://[\w.-]+\.\w+", self.cta_url, re.IGNORECASE):
            errors.append(f"cta_url must be a valid URL, got: '{self.cta_url}'")

        # Valid tone
        valid_tones = {"product_launch", "event", "educational", "feature_update", "reengagement"}
        if self.tone not in valid_tones:
            errors.append(f"tone must be one of {valid_tones}, got: '{self.tone}'")

        # Valid template
        valid_templates = {"product_launch", "event_invite", "educational", "feature_update", "reengagement"}
        if self.template_type not in valid_templates:
            errors.append(f"template_type must be one of {valid_templates}, got: '{self.template_type}'")

        # Cross-field validation: event template needs event date
        if self.template_type == "event_invite" and not self.event_date:
            errors.append("event_date is required for event_invite template")

        # Subject line character limit (will be generated, but flag if brief is too verbose)
        if len(self.key_message) > 200:
            errors.append(f"key_message is {len(self.key_message)} characters — consider shortening for email clarity")

        return errors


def parse_brief_from_markdown(markdown_text: str) -> EmailBrief:
    """
    Parse a markdown brief into a structured EmailBrief.
    Expects a simple format:

    # Campaign Name
    **Audience:** ...
    **Goal:** ...
    **Key Message:** ...
    **CTA:** ... -> ...
    **Tone:** ...
    **Template:** ...
    **Context:** ... (optional)
    """
    lines = markdown_text.strip().split('\n')
    data = {}

    # First # line is campaign name
    for line in lines:
        if line.startswith('# '):
            data['campaign_name'] = line[2:].strip()
            break

    for line in lines:
        line = line.strip()
        if line.startswith('**Audience:**'):
            data['audience'] = line.replace('**Audience:**', '').strip()
        elif line.startswith('**Goal:**'):
            data['goal'] = line.replace('**Goal:**', '').strip()
        elif line.startswith('**Key Message:**'):
            data['key_message'] = line.replace('**Key Message:**', '').strip()
        elif line.startswith('**CTA:**'):
            cta_parts = line.replace('**CTA:**', '').strip()
            # Handle both → (unicode arrow) and -> (ascii arrow)
            separator = None
            if '→' in cta_parts:
                separator = '→'
            elif '->' in cta_parts:
                separator = '->'
            if separator:
                cta_text, cta_url = cta_parts.split(separator, 1)
                data['cta_text'] = cta_text.strip()
                data['cta_url'] = cta_url.strip()
        elif line.startswith('**Tone:**'):
            data['tone'] = line.replace('**Tone:**', '').strip().lower().replace(' ', '_')
        elif line.startswith('**Template:**'):
            data['template_type'] = line.replace('**Template:**', '').strip().lower().replace(' ', '_').replace('-', '_')
        elif line.startswith('**Context:**'):
            data['additional_context'] = line.replace('**Context:**', '').strip()
        elif line.startswith('**Event Date:**'):
            data['event_date'] = line.replace('**Event Date:**', '').strip()
        elif line.startswith('**Hero Image:**'):
            data['hero_image_url'] = line.replace('**Hero Image:**', '').strip()

    # Set defaults for missing fields
    data.setdefault('campaign_name', '')
    data.setdefault('audience', '')
    data.setdefault('goal', '')
    data.setdefault('key_message', '')
    data.setdefault('cta_text', '')
    data.setdefault('cta_url', '')
    data.setdefault('tone', 'educational')
    data.setdefault('template_type', 'educational')
    data.setdefault('additional_context', '')

    return EmailBrief(**{k: v for k, v in data.items() if k in EmailBrief.__dataclass_fields__})


def parse_brief_from_json(json_text: str) -> EmailBrief:
    """Parse a JSON brief into a structured EmailBrief."""
    data = json.loads(json_text)
    valid_fields = {f for f in EmailBrief.__dataclass_fields__}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return EmailBrief(**filtered)
