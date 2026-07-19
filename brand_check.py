"""
Brand Check — Deterministic validation of generated email against brand rules.

All rules are enforced IN CODE, not in the LLM.
The model should never be asked "is this on-brand?" — that's what this module is for.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrandViolation:
    rule: str
    severity: str  # critical, warning, suggestion
    detail: str
    location: str  # subject_line, preview, body, cta, footer


@dataclass
class BrandCheckReport:
    passed: bool
    violations: list[BrandViolation] = field(default_factory=list)
    warnings: list[BrandViolation] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def has_critical(self) -> bool:
        return self.critical_count > 0


class BrandChecker:
    """Deterministic brand compliance validator."""

    # Figma brand colors (from context/brand-guidelines.md)
    BRAND_COLORS = {
        # Core palette
        "#000000", "#1E1E1E", "#0D99FF", "#9747FF", "#FFFFFF", "#F5F5F5",
        # Extended logo palette
        "#00B6FF", "#24CB71", "#FF7237", "#FF3737", "#874FFF",
        # UI tints
        "#E5F4FF", "#CFF7D3", "#F1E5FF", "#FFDFCC", "#FFE0FC", "#EBEBFF", "#E3ECF2",
    }

    # Colors NOT allowed for CTAs or positive actions
    NEGATIVE_COLORS = {"#FF3737", "#FF7237", "#F24822"}

    # The canonical Figma CTA blue
    CTA_COLOR = "#0D99FF"

    REQUIRED_ELEMENTS = [
        ("Figma logo", r'figma\.com', "Must link to figma.com somewhere"),
        ("Unsubscribe link", r'unsubscribe', "Must include unsubscribe mechanism"),
        ("View in browser link", r'view.*browser|web.*version', "Must include view-in-browser link"),
        ("Alt text on all images", r'alt=', "All <img> tags must have alt attributes"),
    ]

    FORBIDDEN_PHRASES = [
        "revolutionary", "game-changing", "disruptive",
        "we're excited to announce",
        "in today's fast-paced world",
        "best-in-class", "industry-leading",
        "synergy", "circle back", "deep dive",
    ]

    FORBIDDEN_PATTERNS = [
        (r'click\s*here', "Forbidden: 'click here' as link text"),
        (r'<img[^>]*?(?<!\balt=)', "Missing alt text on image"),  # Will be caught differently
    ]

    def __init__(self):
        self.violations: list[BrandViolation] = []
        self.warnings: list[BrandViolation] = []

    def check(self, subject_line: str, html_body: str, plain_text: str) -> BrandCheckReport:
        """Run all brand checks. Returns a BrandCheckReport."""
        self.violations = []
        self.warnings = []

        self._check_logo_present(html_body)
        self._check_unsubscribe(html_body, plain_text)
        self._check_view_in_browser(html_body)
        self._check_alt_text(html_body)
        self._check_forbidden_phrases(subject_line, html_body, plain_text)
        self._check_cta_color(html_body)
        self._check_font_family(html_body)
        self._check_color_usage(html_body)
        self._check_all_caps_body(html_body)
        self._check_exclamation_marks(subject_line, html_body)
        self._check_subject_length(subject_line)

        passed = not any(v.severity == "critical" for v in self.violations)

        return BrandCheckReport(
            passed=passed,
            violations=[v for v in self.violations if v.severity == "critical"],
            warnings=[v for v in self.violations if v.severity != "critical"] + self.warnings
        )

    def _add(self, severity: str, rule: str, detail: str, location: str):
        self.violations.append(BrandViolation(rule=rule, severity=severity, detail=detail, location=location))

    def _check_logo_present(self, html: str):
        if 'figma.com' not in html.lower():
            self._add("critical", "Logo link missing", "Must include a link to figma.com (logo)", "body")

    def _check_unsubscribe(self, html: str, plain: str):
        combined = (html + plain).lower()
        if 'unsubscribe' not in combined:
            self._add("critical", "Unsubscribe missing", "Every email must include an unsubscribe link", "footer")

    def _check_view_in_browser(self, html: str):
        lower = html.lower()
        if 'view' not in lower or ('browser' not in lower and 'web' not in lower):
            self._add("warning", "View-in-browser missing", "Include a 'View in browser' link at top", "body")

    def _check_alt_text(self, html: str):
        # Find <img tags and check for alt attribute
        img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
        for i, tag in enumerate(img_tags):
            if 'alt=' not in tag:
                self._add("critical", f"Missing alt text on image {i+1}", f"<img> tag without alt attribute: {tag[:60]}...", "body")

    def _check_forbidden_phrases(self, subject: str, html: str, plain: str):
        combined = (subject + ' ' + html + ' ' + plain).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined:
                self._add("warning", f"Forbidden phrase: '{phrase}'", f"Remove '{phrase}' from copy", "body")

    def _check_cta_color(self, html: str):
        # Check if buttons use the correct Figma CTA blue #0D99FF
        # Look for background-color: #0D99FF or bgcolor="#0D99FF" on buttons/CTAs
        buttons = re.findall(r'<(?:a|button|td)[^>]*?(?:background(?:-color)?\s*:\s*|bgcolor\s*=\s*["\']?)(#[0-9a-fA-F]{6})', html, re.IGNORECASE)
        if buttons:
            for color in buttons:
                if color.upper() != self.CTA_COLOR.upper():
                    self._add("warning", f"CTA color should be Figma Blue (#0D99FF)", f"Button uses {color}, expected {self.CTA_COLOR}", "cta")

    def _check_font_family(self, html: str):
        # Check that fonts used are Helvetica Neue, Arial, or sans-serif
        fonts = re.findall(r'font-family\s*:\s*([^;]+)', html, re.IGNORECASE)
        for font_stack in fonts:
            has_allowed = any(
                f.strip().lower().replace('"', '').replace("'", '') in
                ['helvetica neue', 'helvetica', 'arial', 'sans-serif']
                for f in font_stack.split(',')
            )
            if not has_allowed:
                self._add("critical", f"Invalid font: {font_stack.strip()}", "Use Helvetica Neue, Arial, or sans-serif only", "body")

    def _check_color_usage(self, html: str):
        # Red (#F24822) should only appear in critical alerts
        if '#F24822' in html.upper() or '#f24822' in html.lower():
            # Check context — is it in an alert/error element?
            if 'alert' not in html.lower() and 'error' not in html.lower() and 'warning' not in html.lower():
                self._add("warning", "Red used outside alerts", "#F24822 should only be used for critical alerts", "body")

    def _check_all_caps_body(self, html: str):
        # Remove HTML tags and check text for all-caps runs
        text = re.sub(r'<[^>]+>', ' ', html)
        words = text.split()
        caps_sequences = []
        current_seq = []
        for word in words:
            if word.isupper() and len(word) > 3:
                current_seq.append(word)
            else:
                if len(current_seq) >= 3:
                    caps_sequences.append(' '.join(current_seq))
                current_seq = []
        if len(current_seq) >= 3:
            caps_sequences.append(' '.join(current_seq))

        for seq in caps_sequences:
            if len(seq) > 30:  # Only flag significant runs
                self._add("warning", "All-caps body text", f"All-caps sequence: '{seq[:50]}...'", "body")

    def _check_exclamation_marks(self, subject: str, html: str):
        combined = subject + ' ' + re.sub(r'<[^>]+>', ' ', html)
        count = combined.count('!')
        if count > 2:
            self._add("warning", f"Too many exclamation marks ({count})", "Maximum 2 exclamation marks total", "body")

    def _check_subject_length(self, subject: str):
        if len(subject) > 50:
            self._add("warning", "Subject line too long", f"{len(subject)} characters (limit: 50)", "subject_line")
