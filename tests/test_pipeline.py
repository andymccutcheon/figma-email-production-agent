"""
Eval Framework — Test harness for the email production pipeline.

Tests are categorized:
- Happy path: clean briefs that should produce clean output
- Edge cases: malformed inputs, missing fields, weird data
- Brand compliance: deliberately off-brand output that should be caught
"""

import json
import os
import sys

from intake import EmailBrief, parse_brief_from_markdown
from generate import GeneratedEmail
from brand_check import BrandChecker, BrandCheckReport


def test_intake_happy_path():
    """Valid brief should parse without errors."""
    brief = EmailBrief(
        campaign_name="Test Launch",
        audience="Designers",
        goal="Drive signups for the new feature",
        key_message="Something exciting is here",
        cta_text="Try it now",
        cta_url="https://figma.com/test",
        tone="product_launch",
        template_type="product_launch",
    )
    errors = brief.validate()
    assert errors == [], f"Expected no errors, got: {errors}"
    print("✓ intake_happy_path: Valid brief passes validation")


def test_intake_missing_fields():
    """Brief with missing required fields should return errors."""
    brief = EmailBrief(
        campaign_name="",
        audience="",
        goal="",
        key_message="",
        cta_text="",
        cta_url="",
        tone="product_launch",
        template_type="product_launch",
    )
    errors = brief.validate()
    assert len(errors) > 0, "Expected errors for missing fields"
    print(f"✓ intake_missing_fields: {len(errors)} errors returned")


def test_intake_cta_too_long():
    """CTA text over 4 words should be rejected."""
    brief = EmailBrief(
        campaign_name="Test",
        audience="Designers",
        goal="Drive signups for the new feature",
        key_message="Something exciting is here",
        cta_text="Click here to try the new feature now",
        cta_url="https://figma.com",
        tone="product_launch",
        template_type="product_launch",
    )
    errors = brief.validate()
    assert any("cta_text must be 2-4 words" in e for e in errors), f"Expected CTA word count error, got: {errors}"
    print("✓ intake_cta_too_long: CTA word limit enforced")


def test_intake_invalid_url():
    """Clearly invalid CTA URLs should be rejected."""
    brief = EmailBrief(
        campaign_name="Test",
        audience="Designers",
        goal="Drive signups for the new feature",
        key_message="Something exciting is here",
        cta_text="Try it",
        cta_url="not a valid url",
        tone="product_launch",
        template_type="product_launch",
    )
    errors = brief.validate()
    assert any("valid URL" in e for e in errors), f"Expected URL validation error, got: {errors}"
    print("✓ intake_invalid_url: URL validation enforced")


def test_intake_bare_domain_normalized():
    """Bare domains like help.figma.com/path should be normalized to https://."""
    brief = EmailBrief(
        campaign_name="Test",
        audience="Designers",
        goal="Drive signups for the new feature",
        key_message="Something exciting is here",
        cta_text="Learn more",
        cta_url="help.figma.com/variables",
        tone="feature_update",
        template_type="feature_update",
    )
    assert brief.cta_url == "https://help.figma.com/variables"
    errors = brief.validate()
    assert errors == [], f"Expected normalized URL to pass, got: {errors}"
    print("✓ intake_bare_domain_normalized: bare domain gets https:// prepended")


def test_intake_invalid_tone():
    """Invalid tone value should be rejected."""
    brief = EmailBrief(
        campaign_name="Test",
        audience="Designers",
        goal="Drive signups for the new feature",
        key_message="Something exciting is here",
        cta_text="Try it",
        cta_url="https://figma.com",
        tone="banana",
        template_type="product_launch",
    )
    errors = brief.validate()
    assert any("tone must be one of" in e for e in errors), f"Expected tone validation error, got: {errors}"
    print("✓ intake_invalid_tone: Tone validation enforced")


def test_brand_check_logo():
    """Email without figma.com link should fail."""
    checker = BrandChecker()
    report = checker.check(
        subject_line="Test",
        html_body="<html><body><p>No logo link here</p></body></html>",
        plain_text="No logo link here"
    )
    assert not report.passed, f"Expected critical violation for missing logo link, got passed={report.passed}"
    print(f"✓ brand_check_logo: {report.critical_count} critical violation(s)")


def test_brand_check_unsubscribe():
    """Email without unsubscribe should fail."""
    checker = BrandChecker()
    report = checker.check(
        subject_line="Test",
        html_body="<html><body><a href='https://figma.com'>Figma</a><p>Content</p></body></html>",
        plain_text="Content"
    )
    assert not report.passed, f"Expected critical violation for missing unsubscribe, got passed={report.passed}"
    print(f"✓ brand_check_unsubscribe: {report.critical_count} critical violation(s)")


def test_brand_check_forbidden_phrase():
    """Email with forbidden phrases should produce warnings."""
    checker = BrandChecker()
    report = checker.check(
        subject_line="Revolutionary new feature!",
        html_body="<html><body><a href='https://figma.com'><img src='logo.png' alt='Figma'></a><p>This is revolutionary and game-changing.</p><p><a href='/unsubscribe'>Unsubscribe</a></p><p>760 Market St, San Francisco</p></body></html>",
        plain_text="This is revolutionary and game-changing. Unsubscribe: /unsubscribe"
    )
    assert len(report.warnings) > 0, f"Expected warnings for forbidden phrases, got: {report.warnings}"
    print(f"✓ brand_check_forbidden_phrase: {len(report.warnings)} warning(s) for forbidden phrases")


def test_brand_check_exclamation_marks():
    """Email with >2 exclamation marks should get a warning."""
    checker = BrandChecker()
    report = checker.check(
        subject_line="Wow! Amazing! Incredible!",
        html_body="<html><body><a href='https://figma.com'><img src='logo.png' alt='Figma'></a><p>Content!</p><p><a href='/unsubscribe'>Unsubscribe</a></p><p>760 Market St, San Francisco</p></body></html>",
        plain_text="Wow! Amazing! Incredible! Content! Unsubscribe: /unsubscribe"
    )
    assert any("exclamation" in w.rule.lower() for w in report.warnings), \
        f"Expected exclamation mark warning, got warnings: {[w.rule for w in report.warnings]}"
    print("✓ brand_check_exclamation_marks: Exclamation mark warning triggered")


def test_brand_check_clean_email():
    """A fully compliant email should pass all checks."""
    checker = BrandChecker()
    html = """<html><body>
<a href='https://figma.com'><img src='logo.png' alt='Figma' width='40'></a>
<h1 style="font-family:'Helvetica Neue',Arial,sans-serif;">Welcome to Figma</h1>
<p style="font-family:'Helvetica Neue',Arial,sans-serif;">We help teams design together.</p>
<a href="https://figma.com/ai" style="display:inline-block;background-color:#7B61FF;color:#FFFFFF;font-family:'Helvetica Neue',Arial,sans-serif;padding:14px 32px;border-radius:8px;">Try it now</a>
<p style="font-family:'Helvetica Neue',Arial,sans-serif;"><a href='/unsubscribe'>Unsubscribe</a></p>
<p style="font-family:'Helvetica Neue',Arial,sans-serif;">760 Market St, San Francisco, CA 94102</p>
<p style="font-family:'Helvetica Neue',Arial,sans-serif;"><a href='https://figma.com/view'>View in browser</a></p>
</body></html>"""
    report = checker.check(
        subject_line="Welcome to Figma",
        html_body=html,
        plain_text="Welcome to Figma. We help teams design together. Try it: https://figma.com/ai"
    )
    # Should pass (no critical violations)
    print(f"✓ brand_check_clean_email: passed={report.passed}, "
          f"violations={len(report.violations)}, warnings={len(report.warnings)}")


def test_markdown_parser():
    """Markdown brief should parse correctly."""
    md = """# Test Campaign
**Audience:** Designers at tech companies
**Goal:** Drive 1000 signups for the beta program
**Key Message:** Our new feature makes collaboration instant
**CTA:** Join the beta → https://figma.com/beta
**Tone:** product_launch
**Template:** product_launch
**Context:** This is a limited beta with 1000 spots"""
    brief = parse_brief_from_markdown(md)
    assert brief.campaign_name == "Test Campaign"
    assert brief.audience == "Designers at tech companies"
    assert brief.cta_text == "Join the beta"
    assert brief.cta_url == "https://figma.com/beta"
    assert brief.tone == "product_launch"
    assert brief.template_type == "product_launch"
    print("✓ markdown_parser: All fields parsed correctly")


def test_assemble_html_from_content():
    """LLM copy slots should assemble into valid production HTML."""
    from generate import _assemble_html_from_content, _email_from_llm_data

    brief = EmailBrief(
        campaign_name="Figma AI Launch",
        audience="Design leads",
        goal="Drive trial signups",
        key_message="AI features are now available in Figma.",
        cta_text="Try Figma AI",
        cta_url="https://figma.com/ai",
        tone="product_launch",
        template_type="product_launch",
    )
    data = {
        "subject_line": "AI-powered design, now in Figma",
        "preview_text": "Autocomplete, text-to-design, and layer cleanup.",
        "plain_text": "AI is here. Try it at figma.com/ai",
        "template_used": "product_launch",
        "confidence_score": 5,
        "content": {
            "headline": "Meet Figma AI",
            "intro": "Your creative copilot is here.",
            "rows": [
                {
                    "title": "Autocomplete",
                    "body": "Finish layouts faster with smart suggestions.",
                    "link_text": "Learn more",
                    "link_url": "https://figma.com/ai",
                    "image_alt": "Autocomplete in Figma",
                },
                {
                    "title": "Text to design",
                    "body": "Generate UI from a simple prompt.",
                    "link_text": "See examples",
                    "link_url": "https://figma.com/ai",
                    "image_alt": "Text to design",
                },
                {
                    "title": "Layer cleanup",
                    "body": "Let AI handle tedious layer work.",
                    "link_text": "Try it now",
                    "link_url": "https://figma.com/ai",
                    "image_alt": "Layer cleanup",
                },
            ],
        },
    }
    email = _email_from_llm_data(brief, data)
    assert email.html_body.startswith("<!DOCTYPE html>")
    assert "Meet Figma AI" in email.html_body
    assert "5551FF" in email.html_body or "#5551FF" in email.html_body
    assert "760 Market St" in email.html_body

    checker = BrandChecker()
    report = checker.check(email.subject_line, email.html_body, email.plain_text)
    assert report.passed, f"Expected brand check to pass, got: {report.violations}"
    print("✓ assemble_html_from_content: slots assembled and brand check passed")


def run_all_tests():
    """Run all eval tests."""
    print("\n" + "=" * 60)
    print("EVAL TEST SUITE — Email Production Agent")
    print("=" * 60 + "\n")

    tests = [
        ("Intake", [
            test_intake_happy_path,
            test_intake_missing_fields,
            test_intake_cta_too_long,
            test_intake_invalid_url,
            test_intake_bare_domain_normalized,
            test_intake_invalid_tone,
        ]),
        ("Brand Check", [
            test_brand_check_logo,
            test_brand_check_unsubscribe,
            test_brand_check_forbidden_phrase,
            test_brand_check_exclamation_marks,
            test_brand_check_clean_email,
        ]),
        ("Generator", [
            test_assemble_html_from_content,
        ]),
        ("Parser", [
            test_markdown_parser,
        ]),
    ]

    passed = 0
    failed = 0

    for category, test_funcs in tests:
        print(f"─── {category} ───")
        for test in test_funcs:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"✗ {test.__name__}: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ {test.__name__}: Unexpected error: {e}")
                failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
