"""
Customer.io Sync — Push generated email to Customer.io Design Studio.

Uses the Customer.io REST API directly (no CLI dependency).
Falls back to stub mode when credentials aren't configured.
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
    or os.environ.get("CUSTOMERIO_SITE_ID")
    or os.environ.get("CUSTOMER_IO_SITE_ID")
    or ""
)
CUSTOMER_IO_API_KEY = (
    os.environ.get("CUSTOMERIO_API_KEY")
    or os.environ.get("CUSTOMER_IO_API_KEY")
    or ""
)
CUSTOMER_IO_BASE_URL = os.environ.get(
    "CUSTOMER_IO_BASE_URL",
    "https://api.customer.io/v1",
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
    """Create the email in Customer.io Design Studio via direct REST API call."""

    try:
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError

        payload = json.dumps({
            "name": brief.campaign_name,
            "content": {
                "subject": email.subject_line,
                "preheader_text": email.preview_text,
                "html": email.html_body,
                "text": email.plain_text,
            },
        }, ensure_ascii=False).encode("utf-8")

        endpoint = (
            f"{CUSTOMER_IO_BASE_URL}"
            f"/environments/{CUSTOMER_IO_ENV_ID}"
            f"/design_studio/emails"
        )
        req = Request(endpoint, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {CUSTOMER_IO_API_KEY}")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("User-Agent", "figma-email-agent/1.0")

        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))

        email_data = data.get("email", data)
        email_id = email_data.get("id")

        preview_url = None
        if email_id:
            preview_url = (
                f"https://fly.customer.io/workspaces/{CUSTOMER_IO_ENV_ID}"
                f"/design-studio/emails/{email_id}"
            )

        return SyncResult(
            success=True,
            message_id=email_id,
            provider="customer.io",
            detail="Created in Customer.io Design Studio.",
            preview_url=preview_url,
        )

    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail=f"API error ({e.code}): {body}"
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
        detail="No Customer.io credentials configured. Add CUSTOMERIO_ENV_ID and CUSTOMERIO_API_KEY to .env to enable real sync.",
        preview_url=None,
    )
