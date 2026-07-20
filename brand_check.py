"""
Brand Check — Deterministic validation of generated email against brand rules
and accessibility standards.

All rules are enforced IN CODE, not in the LLM. This module catches what regex
can: structural issues, color violations, missing elements, and accessibility gaps.

Sources: Figma brand guidelines, email-best-practices skill (accessibility rules).
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrandViolation:
    rule: str
    severity: str  # critical, warning, suggestion
    detail: str
    location: str  # subject_line, preview, body, cta, footer, heading, image, table


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
    """Deterministic brand compliance + accessibility validator."""

    # Figma brand colors
    BRAND_COLORS = {
        "#000000", "#1E1E1E", "#0D99FF", "#5551FF", "#699BF7", "#9747FF", "#FFFFFF", "#F5F5F5",
        "#a5a5a5", "#B2B2B2", "#DEDEDE",
        "#00B6FF", "#24CB71", "#FF7237", "#FF3737", "#874FFF",
        "#E5F4FF", "#CFF7D3", "#F1E5FF", "#FFDFCC", "#FFE0FC", "#EBEBFF", "#E3ECF2",
    }

    NEGATIVE_COLORS = {"#FF3737", "#FF7237", "#F24822"}
    PRODUCTION_CTA_COLORS = {"#5551FF", "#000000", "#FFFFFF"}
    LEGACY_CTA_COLOR = "#0D99FF"

    ALLOWED_FONTS = {
        'whyte', 'inter', 'helvetica neue', 'helvetica', 'arial', 'sans-serif',
        'figma standard text',
    }

    FORBIDDEN_PHRASES = [
        "revolutionary", "game-changing", "disruptive",
        "we're excited to announce",
        "in today's fast-paced world",
        "best-in-class", "industry-leading",
        "synergy", "circle back", "deep dive",
    ]

    # Accessibility: vague link text patterns
    VAGUE_LINK_PATTERNS = [
        r'^\s*click\s+here\s*$',
        r'^\s*read\s+more\s*$',
        r'^\s*here\s*$',
        r'^\s*learn\s+more\s*$',
    ]

    # Accessibility: minimum contrast ratio warning threshold (4.5:1 for normal text)
    # These are common low-contrast combinations we flag
    LOW_CONTRAST_PAIRS = [
        ("#666666", "#F5F5F5"),  # gray on light gray
        ("#999999", "#FFFFFF"),  # light gray on white
        ("#AEAEB7", "#FFFFFF"),  # muted gray on white
        ("#D1D1D8", "#FFFFFF"),  # very light gray on white
    ]

    def __init__(self):
        self.violations: list[BrandViolation] = []
        self.warnings: list[BrandViolation] = []

    def check(self, subject_line: str, html_body: str, plain_text: str) -> BrandCheckReport:
        """Run all checks. Returns a BrandCheckReport."""
        self.violations = []
        self.warnings = []

        # Brand checks
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

        # Accessibility checks (from email-best-practices skill)
        self._check_heading_hierarchy(html_body)
        self._check_layout_tables(html_body)
        self._check_link_text_descriptive(html_body)
        self._check_title_tag(html_body)
        self._check_lang_attribute(html_body)

        passed = not any(v.severity == "critical" for v in self.violations)

        return BrandCheckReport(
            passed=passed,
            violations=[v for v in self.violations if v.severity == "critical"],
            warnings=[v for v in self.violations if v.severity != "critical"] + self.warnings
        )

    def _add(self, severity: str, rule: str, detail: str, location: str):
        self.violations.append(BrandViolation(rule=rule, severity=severity, detail=detail, location=location))

    # ── Brand Checks ──────────────────────────────────────

    def _check_logo_present(self, html: str):
        if 'figma.com' not in html.lower():
            self._add("critical", "Logo link missing", "Must include a link to figma.com (logo)", "body")

    def _check_unsubscribe(self, html: str, plain: str):
        combined = (html + plain).lower()
        if 'unsubscribe' not in combined:
            self._add("critical", "Unsubscribe missing", "Every email must include an unsubscribe link", "footer")

    def _check_view_in_browser(self, html: str):
        """View-in-browser is optional in v4.0 production emails."""
        pass

    def _check_cta_color(self, html: str):
        buttons = re.findall(
            r'<(?:a|button|td)[^>]*?(?:background(?:-color)?\s*:\s*|bgcolor\s*=\s*["\']?)(#[0-9a-fA-F]{6})',
            html, re.IGNORECASE
        )
        brand_upper = {c.upper() for c in self.BRAND_COLORS}
        allowed = self.PRODUCTION_CTA_COLORS | {self.LEGACY_CTA_COLOR}
        for color in buttons:
            upper = color.upper()
            if upper in {c.upper() for c in allowed}:
                continue
            if upper not in brand_upper:
                self._add("warning", f"Non-standard CTA color: {color}",
                          "Production CTAs use #5551FF (lifecycle) or #000000 (newsletter)", "cta")

    def _check_alt_text(self, html: str):
        img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
        for i, tag in enumerate(img_tags):
            if 'alt=' not in tag:
                self._add("critical", f"Missing alt text on image {i+1}",
                          f"<img> tag without alt attribute: {tag[:80]}...", "image")
            elif 'alt=""' not in tag and "alt=''" not in tag:
                alt_match = re.search(r'alt=["\']([^"\']*)["\']', tag)
                if alt_match:
                    alt_value = alt_match.group(1).strip()
                    if alt_value and len(alt_value) < 3:
                        self._add("warning", f"Alt text too short on image {i+1}",
                                  f"Alt text '{alt_value}' is very short — describe the image's purpose", "image")

    def _check_font_family(self, html: str):
        fonts = re.findall(r'(?<!mso-generic-)font-family\s*:\s*([^;]+)', html, re.IGNORECASE)
        for font_stack in fonts:
            has_allowed = any(
                f.strip().lower().replace('"', '').replace("'", '') in self.ALLOWED_FONTS
                for f in font_stack.split(',')
            )
            if not has_allowed:
                self._add("critical", f"Invalid font: {font_stack.strip()}",
                          "Use Whyte, Inter, Helvetica Neue, Arial, or sans-serif", "body")

    def _check_forbidden_phrases(self, subject: str, html: str, plain: str):
        combined = (subject + ' ' + html + ' ' + plain).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined:
                self._add("warning", f"Forbidden phrase: '{phrase}'",
                          f"Remove '{phrase}' from copy", "body")

    def _check_color_usage(self, html: str):
        if '#F24822' in html.upper() or '#f24822' in html.lower():
            if 'alert' not in html.lower() and 'error' not in html.lower():
                self._add("warning", "Red used outside alerts",
                          "#F24822 should only be used for critical alerts", "body")

    def _check_all_caps_body(self, html: str):
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
            if len(seq) > 30:
                self._add("warning", "All-caps body text",
                          f"All-caps sequence: '{seq[:50]}...'", "body")

    def _check_exclamation_marks(self, subject: str, html: str):
        html_no_style = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        body_text = re.sub(r'<[^>]+>', ' ', html_no_style)
        combined = subject + ' ' + body_text
        count = combined.count('!')
        if count > 2:
            self._add("warning", f"Too many exclamation marks ({count})",
                      "Maximum 2 exclamation marks total", "body")

    def _check_subject_length(self, subject: str):
        if len(subject) > 50:
            self._add("warning", "Subject line too long",
                      f"{len(subject)} characters (limit: 50)", "subject_line")

    # ── Accessibility Checks ──────────────────────────────

    def _check_heading_hierarchy(self, html: str):
        """Check heading structure: single h1, no skipped levels, at least one heading.
        Also detects MJML-compiled emails where headings are styled divs/p tags.
        """
        headings = re.findall(r'<h([1-6])\b[^>]*>', html, re.IGNORECASE)
        levels = [int(h) for h in headings]

        if not levels:
            # No semantic headings — check for visual headings in MJML-compiled output
            # Look for elements with large font-size and bold (heading-equivalent)
            heading_styled = re.findall(
                r'font-size\s*:\s*2[4-9]px|font-size\s*:\s*[3-9]\dpx',
                html, re.IGNORECASE
            )
            if not heading_styled:
                self._add("warning", "No headings found",
                          "Add at least one large, bold heading for visual hierarchy and screen reader navigation", "heading")
            return

        h1_count = levels.count(1)
        if h1_count == 0:
            self._add("warning", "Missing <h1>",
                      "Every email should have a single <h1> for the main heading", "heading")
        elif h1_count > 1:
            self._add("warning", f"Multiple <h1> tags ({h1_count})",
                      "Use a single <h1> — nest subheadings with h2, h3, etc.", "heading")

        # Check for skipped levels
        for i in range(len(levels) - 1):
            if levels[i + 1] - levels[i] > 1:
                self._add("suggestion", f"Heading skip: h{levels[i]} → h{levels[i+1]}",
                          "Don't skip heading levels (e.g., h2 → h4 without h3)", "heading")

    def _check_layout_tables(self, html: str):
        """Check that layout tables have role='presentation'."""
        tables = re.findall(r'<table\b([^>]*)>', html, re.IGNORECASE)
        for i, attrs in enumerate(tables):
            if not re.search(r'role\s*=\s*["\']presentation["\']', attrs, re.IGNORECASE):
                self._add("warning", f"Table {i+1} missing role='presentation'",
                          "Layout tables should have role='presentation' for screen readers", "table")

    def _check_link_text_descriptive(self, html: str):
        """Check links for vague text like 'click here' or 'read more'."""
        links = re.findall(r'<a\b[^>]*>([^<]*)</a>', html, re.IGNORECASE)
        for text in links:
            text = text.strip()
            if not text:
                # Empty link text — might be an image-only link
                continue
            for pattern in self.VAGUE_LINK_PATTERNS:
                if re.match(pattern, text, re.IGNORECASE):
                    self._add("warning", f"Vague link text: '{text}'",
                              "Link text should describe the destination, not 'click here'", "body")
                    break

    def _check_title_tag(self, html: str):
        """Check for <title> tag in the HTML head."""
        if not re.search(r'<title[^>]*>', html, re.IGNORECASE):
            self._add("warning", "Missing <title> tag",
                      "Every email should have a <title> for accessibility and preview", "body")

    def _check_lang_attribute(self, html: str):
        """Check for lang attribute on <html> or <mjml> tag."""
        html_tag = re.search(r'<(?:html|mjml)\b([^>]*)>', html, re.IGNORECASE)
        if html_tag:
            attrs = html_tag.group(1)
            if 'lang=' not in attrs.lower():
                self._add("warning", "Missing lang attribute",
                          "Set lang='en' on the root element for screen readers", "body")
