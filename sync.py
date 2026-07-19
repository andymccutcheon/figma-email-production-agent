"""
Customer.io Sync — Push generated email to Customer.io for final review.

Uses the cio CLI (Customer.io's official CLI) to create emails in Design Studio.
Falls back to stub mode when credentials aren't configured or CLI isn't installed.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

from generate import GeneratedEmail
from intake import EmailBrief

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Customer.io configuration ──────────────────────────────
CUSTOMER_IO_ENV_ID = (
    os.environ.get("CUSTOMERIO_ENV_ID")
    or os.environ.get("CUSTOMER_IO_ENVIRONMENT_ID")
    or os.environ.get("CUSTOMER_IO_ENV_ID")
    or ""
)
CUSTOMER_IO_API_KEY = (
    os.environ.get("CUSTOMERIO_API_KEY")
    or os.environ.get("CUSTOMER_IO_API_KEY")
    or ""
)
CUSTOMER_IO_BASE_URL = os.environ.get(
    "CUSTOMER_IO_BASE_URL",
    "https://us.fly.customer.io/v1"
)


@dataclass
class SyncResult:
    success: bool
    message_id: Optional[str]
    provider: str
    detail: str
    preview_url: Optional[str] = None


def sync_to_customer_io(email: GeneratedEmail, brief: EmailBrief) -> SyncResult:
    """Push the generated email to Customer.io as a Design Studio email."""
    if not CUSTOMER_IO_ENV_ID or not CUSTOMER_IO_API_KEY:
        return _sync_stub(email, brief)

    return _sync_real(email, brief)


def _sync_real(email: GeneratedEmail, brief: EmailBrief) -> SyncResult:
    """Create the email in Customer.io Design Studio via the cio CLI."""

    payload = json.dumps({
        "name": brief.campaign_name,
        "content": {
            "subject": email.subject_line,
            "preheader_text": email.preview_text,
            "html": email.html_body,
            "text": email.plain_text,
        },
    })

    try:
        import subprocess

        result = subprocess.run(
            [
                "cio", "api",
                f"/v1/environments/{CUSTOMER_IO_ENV_ID}/design_studio/emails",
                "-X", "POST",
                "--json", payload,
                "--token", CUSTOMER_IO_API_KEY,
                "--timeout", "30s",
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )

        if result.returncode != 0:
            # Try to parse error from stderr/stdout
            try:
                err = json.loads(result.stdout or result.stderr)
                msg = err.get("error", {}).get("message", result.stderr[:300])
            except json.JSONDecodeError:
                msg = (result.stderr or result.stdout)[:300]
            return SyncResult(
                success=False, message_id=None, provider="customer.io",
                detail=f"CLI error: {msg}"
            )

        data = json.loads(result.stdout)
        email_data = data.get("email", data)
        email_id = email_data.get("id")

        return SyncResult(
            success=True,
            message_id=email_id,
            provider="customer.io",
            detail=f"Created in Customer.io Design Studio.",
            preview_url=f"https://fly.customer.io/workspaces/{CUSTOMER_IO_ENV_ID}/design-studio/emails/{email_id}" if email_id else None,
        )

    except FileNotFoundError:
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail="cio CLI not found. Install with: npm install -g @customerio/customerio-cli"
        )
    except subprocess.TimeoutExpired:
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail="Customer.io API request timed out (30s)."
        )
    except Exception as e:
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail=f"Unexpected error: {str(e)}"
        )


def _sync_stub(email: GeneratedEmail, brief: EmailBrief) -> SyncResult:
    """Stub sync for when Customer.io credentials aren't configured."""
    return SyncResult(
        success=True,
        message_id=f"ci_stub_{brief.campaign_name.lower().replace(' ', '_')}_001",
        provider="customer.io (stub)",
        detail="No Customer.io credentials configured. Add CUSTOMER_IO_SITE_ID and CUSTOMER_IO_API_KEY to .env to enable real sync.",
        preview_url=None,
    )
