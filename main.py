#!/usr/bin/env python3
"""
Email Production Agent — Main Entry Point

Usage:
    # Run with sample briefs in demo mode (no API key needed)
    python3 main.py

    # Run with a custom brief file
    python3 main.py --brief path/to/brief.md

    # Run with Anthropic API (real LLM generation)
    python3 main.py --api-key $ANTHROPIC_API_KEY

    # Run with auto-approve (skip human review, sync automatically)
    python3 main.py --auto-approve

Sample briefs are in tests/sample-briefs/.
"""

import argparse
import os
import sys

from orchestrator import run_pipeline
from generate import get_active_provider


def main():
    parser = argparse.ArgumentParser(description="Figma Email Production Agent")
    parser.add_argument("--brief", help="Path to a brief file (markdown or JSON)")
    parser.add_argument("--api-key", help="Anthropic API key for real LLM generation")
    parser.add_argument("--auto-approve", action="store_true", help="Skip human review and sync automatically")
    parser.add_argument("--sample", type=int, default=1, help="Sample brief number to run (1-3)")
    args = parser.parse_args()

    # Load brief
    if args.brief:
        with open(args.brief) as f:
            brief_text = f.read()
        fmt = "json" if args.brief.endswith(".json") else "markdown"
    else:
        brief_text, fmt = get_sample_brief(args.sample)

    print("=" * 60)
    print("FIGMA EMAIL PRODUCTION AGENT")
    print("=" * 60)
    print(f"Mode: {get_active_provider().title() if get_active_provider() != 'demo' else 'Demo (simulated LLM)'}")
    print()

    # Run pipeline
    result = run_pipeline(
        brief_input=brief_text,
        input_format=fmt,
        api_key=args.api_key,
        auto_approve=args.auto_approve,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    print(f"Status: {result.status}")

    if result.brief:
        print(f"Campaign: {result.brief.campaign_name}")
        print(f"Audience: {result.brief.audience}")
        print(f"Template: {result.brief.template_type}")

    if result.email:
        print(f"\nSubject: {result.email.subject_line}")
        print(f"Preview: {result.email.preview_text}")
        print(f"Confidence: {result.email.confidence_score}/5")

    if result.brand_report:
        print(f"\nBrand Check: {'PASSED' if result.brand_report.passed else 'FAILED'}")
        if result.brand_report.violations:
            for v in result.brand_report.violations:
                print(f"  ✗ [{v.severity}] {v.rule}")
        if result.brand_report.warnings:
            for w in result.brand_report.warnings:
                print(f"  ⚠ [{w.severity}] {w.rule}")

    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for e in result.errors:
            print(f"  ✗ {e}")

    if result.preview_path:
        print(f"\nPreview: {result.preview_path}")
        print(f"Open it in a browser: file://{os.path.abspath(result.preview_path)}")

    if result.sync_result:
        print(f"\nSync: {result.sync_result.detail}")

    print()


def get_sample_brief(num: int) -> tuple[str, str]:
    """Get a sample brief for demo purposes."""
    samples_dir = os.path.join(os.path.dirname(__file__), "tests", "sample-briefs")
    path = os.path.join(samples_dir, f"brief-{num:02d}.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read(), "markdown"

    # Fallback: inline sample briefs
    samples = {
        1: """# Figma AI Launch
**Audience:** Design leads and heads of design at companies with 50+ employees
**Goal:** Drive trial signups for Figma AI features. We want 500 new AI feature activations in the first week.
**Key Message:** Figma AI is now available — autocomplete your designs, generate variations from text prompts, and let AI handle the tedious layers so you can focus on the creative work.
**CTA:** Try Figma AI → https://figma.com/ai
**Tone:** product_launch
**Template:** product_launch
**Context:** This is our biggest launch of Q3. The AI features have been in beta for 3 months with overwhelmingly positive feedback.""",

        2: """# Config 2026 Early Access
**Audience:** Past Config attendees and Figma power users in US and Europe
**Goal:** Drive early-bird registrations before the general public announcement
**Key Message:** Config is back. Join 10,000+ designers and builders in San Francisco for two days of keynotes, workshops, and the future of design tools.
**CTA:** Register early → https://config.figma.com/2026
**Tone:** event
**Template:** event_invite
**Event Date:** June 10-11, 2026
**Context:** Early bird pricing is $399 (saves $200). We're announcing the keynote speaker lineup next week — registrants hear it first.""",

        3: """# Components Update: Variables Everywhere
**Audience:** All Figma users who have used components in the last 90 days
**Goal:** Drive adoption of the new variables system. Target: 20% of component users try variables within 30 days.
**Key Message:** Variables now work across all component properties — colors, text, visibility, and layout. Build one component, deploy it everywhere, with variations that adapt to any context.
**CTA:** Learn more → https://help.figma.com/variables
**Tone:** feature_update
**Template:** feature_update
**Context:** This was our #1 community request. The old system only supported color variables.""",
    }

    return samples.get(num, samples[1]), "markdown"


if __name__ == "__main__":
    main()
