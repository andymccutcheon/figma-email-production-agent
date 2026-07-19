"""
Preview — Render the generated email and brand report for human review.

This is the human-in-the-loop gate. The email never sends without
a human seeing this preview and explicitly approving it.
"""

import os
from brand_check import BrandCheckReport
from generate import GeneratedEmail


def render_preview(email: GeneratedEmail, brand_report: BrandCheckReport) -> str:
    """Generate an HTML preview page showing the email and brand compliance report side by side."""
    violations_html = ""
    if brand_report.violations:
        violations_html = "<h3 style='color:#F24822;'>❌ Violations</h3><ul style='color:#F24822;'>"
        for v in brand_report.violations:
            violations_html += f"<li><strong>[{v.location}]</strong> {v.rule}: {v.detail}</li>"
        violations_html += "</ul>"

    warnings_html = ""
    if brand_report.warnings:
        warnings_html = "<h3 style='color:#E67E22;'>⚠ Warnings</h3><ul style='color:#E67E22;'>"
        for w in brand_report.warnings:
            warnings_html += f"<li><strong>[{w.location}]</strong> {w.rule}: {w.detail}</li>"
        warnings_html += "</ul>"

    status_color = "#0FA958" if brand_report.passed else "#F24822"
    status_text = "✓ Passed" if brand_report.passed else "✗ Has Critical Violations"

    confidence_color = "#0FA958" if email.confidence_score >= 4 else ("#E67E22" if email.confidence_score >= 3 else "#F24822")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Email Preview — {email.subject_line}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  @font-face {{ font-family: 'Figma Standard Text'; src: url('/static/fonts/Figma-Standard-Text-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
  @font-face {{ font-family: 'Figma Standard Text'; src: url('/static/fonts/Figma-Standard-Text-Medium.woff2') format('woff2'); font-weight: 500; font-display: swap; }}
  @font-face {{ font-family: 'Figma Mono'; src: url('/static/fonts/Figma-Mono-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
  body {{ font-family: 'Figma Standard Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #F5F5F5; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
  .header {{ background: white; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header h1 {{ font-size: 20px; margin-bottom: 8px; }}
  .meta {{ display: flex; gap: 24px; font-size: 14px; color: #666; }}
  .meta-item {{ display: flex; align-items: center; gap: 6px; }}
  .main {{ display: grid; grid-template-columns: 1fr 400px; gap: 20px; align-items: start; }}
  @media (max-width: 900px) {{ .main {{ grid-template-columns: 1fr; }} }}
  .panel {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .panel-header {{ padding: 16px 20px; border-bottom: 1px solid #F5F5F5; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #666; }}
  .panel-body {{ padding: 20px; }}
  .report {{ padding: 0; }}
  .report-section {{ padding: 16px 20px; border-bottom: 1px solid #F5F5F5; }}
  .report-section:last-child {{ border-bottom: none; }}
  .report-section h3 {{ font-size: 14px; margin-bottom: 8px; }}
  .report-section ul {{ list-style: none; padding: 0; }}
  .report-section li {{ padding: 6px 0; font-size: 13px; line-height: 1.5; border-bottom: 1px solid #F5F5F5; }}
  .report-section li:last-child {{ border-bottom: none; }}
  .approve-bar {{ background: white; padding: 16px 24px; border-radius: 8px; margin-top: 20px; display: flex; gap: 12px; align-items: center; justify-content: flex-end; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .btn {{ padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }}
  .btn-approve {{ background: #0FA958; color: white; }}
  .btn-reject {{ background: #F5F5F5; color: #666; }}
  .btn-feedback {{ background: #0D99FF; color: white; }}
  .confidence {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
  iframe {{ width: 100%; height: 600px; border: 1px solid #F5F5F5; border-radius: 4px; }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>📧 {email.subject_line}</h1>
    <div class="meta">
      <span class="meta-item">Template: {email.template_used}</span>
      <span class="meta-item">Brand: <span style="color:{status_color};font-weight:600;">{status_text}</span></span>
      <span class="meta-item">Confidence: <span class="confidence" style="background:{confidence_color}20;color:{confidence_color};">{email.confidence_score}/5</span></span>
    </div>
  </div>

  <!-- Main Grid -->
  <div class="main">

    <!-- Email Preview -->
    <div class="panel">
      <div class="panel-header">Email Preview</div>
      <div class="panel-body" style="padding:0;">
        <iframe srcdoc="{_escape_html(email.html_body)}" sandbox="allow-same-origin"></iframe>
      </div>
    </div>

    <!-- Brand Compliance Report -->
    <div class="panel report">
      <div class="panel-header">Brand Compliance Report</div>
      <div class="report-section">
        {violations_html}
        {warnings_html}
        {f'<p style="color:#0FA958;font-size:14px;">✓ All brand checks passed</p>' if (not brand_report.violations and not brand_report.warnings) else ''}
      </div>
      <div class="report-section">
        <h3>Plain Text Version</h3>
        <pre style="font-size:12px;color:#666;white-space:pre-wrap;font-family:monospace;max-height:200px;overflow-y:auto;">{email.plain_text}</pre>
      </div>
    </div>
  </div>

  <!-- Approval Bar -->
  <div class="approve-bar">
    <span style="font-size:13px;color:#666;margin-right:auto;">This email has NOT been sent. Human review required.</span>
    <button class="btn btn-reject" onclick="alert('In production, this would reject and request regeneration.')">✗ Reject</button>
    <button class="btn btn-feedback" onclick="alert('In production, this would open a feedback form for targeted edits.')">💬 Feedback</button>
    <button class="btn btn-approve" onclick="alert('In production, this would sync to Customer.io for final QA.')">✓ Approve & Sync</button>
  </div>

</div>
</body>
</html>"""
    return html


def save_preview(email: GeneratedEmail, brand_report: BrandCheckReport, output_dir: str = "output") -> str:
    """Save the preview HTML to a file. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)
    html = render_preview(email, brand_report)
    path = os.path.join(output_dir, "email-preview.html")
    with open(path, "w") as f:
        f.write(html)
    return path


def _escape_html(html: str) -> str:
    """Escape HTML for safe embedding in srcdoc attribute."""
    return html.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
