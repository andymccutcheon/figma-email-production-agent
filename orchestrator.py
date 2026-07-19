"""
Orchestrator — Wire the pipeline together.

Coordinates the full email production flow:
1. Parse & validate the brief (deterministic)
2. Generate email (LLM)
3. Brand compliance check (deterministic)
4. Render preview (deterministic)
5. Human review gate (blocking)
6. Sync to Customer.io (deterministic, stubbed)

Each step is independently testable. The orchestrator manages state
and decision points — it doesn't generate or validate anything itself.
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional

from intake import EmailBrief, parse_brief_from_markdown, parse_brief_from_json
from generate import generate_email, GeneratedEmail
from brand_check import BrandChecker, BrandCheckReport
from preview import save_preview
from sync import sync_to_customer_io, SyncResult


@dataclass
class PipelineResult:
    brief: EmailBrief
    email: Optional[GeneratedEmail]
    brand_report: Optional[BrandCheckReport]
    sync_result: Optional[SyncResult]
    preview_path: Optional[str]
    errors: list[str]
    status: str  # validated, generated, reviewed, approved, synced, failed

    def to_dict(self) -> dict:
        return {
            "brief": {k: v for k, v in asdict(self.brief).items()},
            "email": self.email.to_dict() if self.email else None,
            "brand_report": {
                "passed": self.brand_report.passed,
                "critical_count": self.brand_report.critical_count,
                "violations": [asdict(v) for v in self.brand_report.violations],
                "warnings": [asdict(w) for w in self.brand_report.warnings],
            } if self.brand_report else None,
            "sync_result": {
        "success": self.sync_result.success,
        "message_id": self.sync_result.message_id,
        "provider": self.sync_result.provider,
        "detail": self.sync_result.detail,
        "preview_url": self.sync_result.preview_url,
    } if self.sync_result else None,
            "preview_path": self.preview_path,
            "errors": self.errors,
            "status": self.status,
        }


def run_pipeline(brief_input: str, input_format: str = "markdown", api_key: Optional[str] = None, auto_approve: bool = False) -> PipelineResult:
    """
    Run the full email production pipeline.

    Args:
        brief_input: The email brief as markdown or JSON string
        input_format: "markdown" or "json"
        api_key: Optional Anthropic API key for real LLM generation
        auto_approve: If True, skip human review and sync automatically (for testing)

    Returns:
        PipelineResult with full state at each step
    """
    result = PipelineResult(
        brief=None,
        email=None,
        brand_report=None,
        sync_result=None,
        preview_path=None,
        errors=[],
        status="started",
    )

    # ── Step 1: Parse & Validate Brief ─────────────────────────
    try:
        if input_format == "json":
            brief = parse_brief_from_json(brief_input)
        else:
            brief = parse_brief_from_markdown(brief_input)
    except Exception as e:
        result.errors.append(f"Brief parse error: {e}")
        result.status = "failed"
        return result

    errors = brief.validate()
    if errors:
        result.errors.extend(errors)
        result.status = "failed"
        result.brief = brief
        return result

    result.brief = brief
    result.status = "validated"
    print(f"✓ Brief validated: {brief.campaign_name}")

    # ── Step 2: Generate Email ─────────────────────────────────
    try:
        email = generate_email(brief, api_key=api_key)
        result.email = email
        result.status = "generated"
        print(f"✓ Email generated (confidence: {email.confidence_score}/5)")
    except Exception as e:
        result.errors.append(f"Generation error: {e}")
        result.status = "failed"
        return result

    # ── Step 3: Brand Compliance Check ─────────────────────────
    checker = BrandChecker()
    brand_report = checker.check(email.subject_line, email.html_body, email.plain_text)
    result.brand_report = brand_report
    result.status = "reviewed"
    print(f"✓ Brand check: {'PASSED' if brand_report.passed else 'CRITICAL VIOLATIONS'}"
          f" ({len(brand_report.violations)} violations, {len(brand_report.warnings)} warnings)")

    # ── Step 4: Render Preview ─────────────────────────────────
    try:
        preview_path = save_preview(email, brand_report)
        result.preview_path = preview_path
        print(f"✓ Preview saved: {preview_path}")
    except Exception as e:
        result.errors.append(f"Preview error: {e}")
        result.status = "failed"
        return result

    # ── Step 5: Human Review Gate ──────────────────────────────
    # In this POC, the preview page is the gate.
    # In production, this would wait for explicit approval.
    if not auto_approve:
        print("\n─── HUMAN REVIEW REQUIRED ───")
        print(f"Open {preview_path} in a browser to review.")
        print(f"Status: {result.status}")
        print("After review, call sync_to_customer_io() manually or re-run with auto_approve=True")
        return result

    # ── Step 6: Sync to Customer.io ───────────────────────────
    if not brand_report.passed:
        result.errors.append("Cannot sync: brand check has critical violations")
        result.status = "failed"
        return result

    try:
        sync_result = sync_to_customer_io(email, brief)
        result.sync_result = sync_result
        result.status = "synced"
        print(f"✓ Synced to Customer.io: {sync_result.message_id} ({sync_result.detail})")
    except Exception as e:
        result.errors.append(f"Sync error: {e}")
        result.status = "failed"

    return result
