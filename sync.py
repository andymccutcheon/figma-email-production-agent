"""
Customer.io Sync — Push generated email to Customer.io.

Tries multiple approaches in order:
  1. Design Studio API (preferred — app API key required)
  2. Transactional message API (fallback — app API key required)
  3. Stub mode (when credentials are missing or insufficient)

Uses the Customer.io REST API directly (no CLI dependency).
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
# App API key (for transactional / design studio)
CUSTOMER_IO_APP_KEY = (
    os.environ.get("CUSTOMERIO_APP_API_KEY")
    or os.environ.get("CUSTOMER_IO_APP_API_KEY")
    or ""
)
# Server/Track API key (for tracking / campaigns)
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
    """Push the generated email to Customer.io."""
    if not CUSTOMER_IO_ENV_ID:
        return _sync_stub(email, brief, "No Customer.io environment ID configured.")

    # Prefer app API key for Design Studio / transactional
    api_key = CUSTOMER_IO_APP_KEY or CUSTOMER_IO_API_KEY
    if not api_key:
        return _sync_stub(email, brief, "No Customer.io API key configured.")

    # Try Design Studio API first (requires app API key)
    result = _try_design_studio(email, brief, api_key)
    if result.success:
        return result

    # If that failed with auth error, the key type is wrong
    if "401" in result.detail or "unauthorized" in result.detail.lower():
        if not CUSTOMER_IO_APP_KEY:
            return SyncResult(
                success=False,
                message_id=None,
                provider="customer.io",
                detail=(
                    "API key doesn't have Design Studio access. "
                    "Set CUSTOMERIO_APP_API_KEY with an App API key "
                    "from Customer.io Settings → API Credentials."
                ),
            )

    return result


def _try_design_studio(email: GeneratedEmail, brief: EmailBrief, api_key: str) -> SyncResult:
    """Create the email in Customer.io Design Studio via REST API."""
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

        # Try fly.customer.io first (where the Design Studio API lives)
        endpoint = (
            f"https://fly.customer.io/v1"
            f"/environments/{CUSTOMER_IO_ENV_ID}"
            f"/design_studio/emails"
        )
        req = Request(endpoint, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {api_key}")
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
        body = e.read().decode("utf-8", errors="replace")[:300]
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail=f"API error ({e.code}): {body}"
        )
    except Exception as e:
        return SyncResult(
            success=False, message_id=None, provider="customer.io",
            detail=f"Error: {str(e)}"
        )


def _sync_stub(email: GeneratedEmail, brief: EmailBrief, reason: str = "") -> SyncResult:
    """Stub sync for when Customer.io credentials aren't configured or are wrong type."""
    return SyncResult(
        success=True,
        message_id=f"ci_stub_{brief.campaign_name.lower().replace(' ', '_')}_001",
        provider="customer.io (stub)",
        detail=reason or "No Customer.io credentials configured.",
        preview_url=None,
    )
