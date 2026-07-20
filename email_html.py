"""
v4.0 HTML email building blocks — extracted from figma-examples/ production sends.

Two design lineages:
  - Whyte (lifecycle): onboarding, product launch, re-engagement, educational
  - Inter (newsletter): feature updates, release notes
"""

from __future__ import annotations

from typing import Literal, Optional

Lineage = Literal["whyte", "inter"]
CtaStyle = Literal["purple", "outline", "black"]

MAX_WIDTH = 650
WHYTE_STACK = "'Whyte', Helvetica, Arial, sans-serif"
INTER_STACK = "Inter, Helvetica, Arial, sans-serif"
PURPLE = "#5551FF"
BLACK = "#000000"
WHITE = "#FFFFFF"
MUTED = "#a5a5a5"
FOOTER_MUTED = "#B2B2B2"

LOGO_LIGHT = "https://static.figma.com/uploads/f2c739b51898125e6ab81e67036787f570c03b0e"
LOGO_DARK = "https://static.figma.com/uploads/53280c3b3748be75104b3f237318ba3036b959b7"
WHYTE_WOFF = "https://static.figma.com/uploads/9254519927cf4912e61627442d7ab7a5a9226581.woff"

SOCIAL_ICONS = [
    ("Figma", "https://figma.com", "https://static.figma.com/uploads/a9c9c230c0a9395f5eaa1c4acb6ee89d13782987"),
    ("Twitter", "https://twitter.com/figma", "https://static.figma.com/uploads/5bb05074a2c9507b003979dd88c1bb852fb875b7"),
    ("Instagram", "https://instagram.com/figma", "https://static.figma.com/uploads/9dc8394d92432c5cd16ab9e61ee574da29434ec8"),
    ("YouTube", "https://youtube.com/figmadesign", "https://static.figma.com/uploads/4db5401f0db17df56b55b663da4ec93b18f2d707"),
    ("LinkedIn", "https://linkedin.com/company/figma", "https://static.figma.com/uploads/02676955b299a6571870721434fcc596c6b8de56"),
]

PLACEHOLDER_HERO = "https://static.figma.com/uploads/efb8b874cf81705346aeaa7d4d5d65ca23a9836e"
PLACEHOLDER_ROW = "https://static.figma.com/uploads/ebda29ac2a7ddefa6f23c64e6c0514c8e9029ba4"


def _font_stack(lineage: Lineage) -> str:
    return WHYTE_STACK if lineage == "whyte" else INTER_STACK


def _head_css(lineage: Lineage) -> str:
    font_face = f"""@font-face {{
  font-family: 'Whyte';
  font-style: normal;
  font-weight: normal;
  src: url({WHYTE_WOFF}) format('woff');
  mso-font-alt: 'Arial';
}}"""
    if lineage == "inter":
        font_face = """@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/inter/v18/UcCo3FwrK3iLTcviYwYZ8UA3.woff2) format('woff2');
  mso-generic-font-family: swiss;
}"""

    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<style type="text/css">
:root {{ color-scheme: light dark; supported-color-schemes: light dark; }}
{font_face}
table, td {{ mso-table-lspace:0; mso-table-rspace:0; border-spacing:0; border:0; }}
a {{ text-decoration:none; }}
@media screen and (max-width:649px) {{
  .w-100p {{ width:100% !important; }}
  .tflex {{ display:block !important; width:100% !important; }}
}}
@media (prefers-color-scheme:dark) {{
  .darkmode {{ background-color:#000000 !important; }}
  .light-img {{ display:none !important; }}
  .dark-img {{ display:block !important; width:auto !important; overflow:visible !important; max-height:inherit !important; max-width:inherit !important; visibility:inherit !important; }}
}}
[data-ogsc] .light-img {{ display:none !important; }}
[data-ogsc] .dark-img {{ display:block !important; width:auto !important; visibility:inherit !important; }}
[data-ogsc] .darkmode {{ background-color:#000000 !important; }}
</style>"""


def preview_text_div(text: str) -> str:
    spacers = "\u00a0" * 40 + "\u200c" * 20
    return (
        f'<div style="display:none;font-size:1px;color:#ffffff;line-height:1px;'
        f'max-height:0;max-width:0;opacity:0;overflow:hidden;">'
        f'{text}{spacers}</div>'
    )


def logo_block(figma_url: str = "https://figma.com") -> str:
    return f"""<table role="presentation" width="{MAX_WIDTH}" align="center" style="max-width:{MAX_WIDTH}px;margin:0 auto;" cellpadding="0" cellspacing="0">
<tr><td align="left" style="padding:25px 24px 25px 0;">
  <a href="{figma_url}" style="text-decoration:none;">
    <img class="light-img" src="{LOGO_LIGHT}" width="110" alt="Figma" style="width:110px;max-width:110px;border:0;" />
  </a>
  <div class="dark-img" style="display:none;overflow:hidden;max-height:0;max-width:0;visibility:hidden;">
    <a href="{figma_url}"><img src="{LOGO_DARK}" width="110" alt="Figma" style="width:110px;border:0;" /></a>
  </div>
</td></tr></table>"""


def hero_image(url: str, alt: str, link: str = "#") -> str:
    return f"""<table role="presentation" width="{MAX_WIDTH}" align="center" style="max-width:{MAX_WIDTH}px;margin:0 auto;" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:0 0 24px;">
  <a href="{link}"><img src="{url}" width="{MAX_WIDTH}" alt="{alt}" style="width:{MAX_WIDTH}px;max-width:100%;border:0;display:block;" /></a>
</td></tr></table>"""


def headline(text: str, lineage: Lineage = "whyte", size: str = "26px") -> str:
    stack = _font_stack(lineage)
    if lineage == "inter":
        size = "32px"
    return (
        f'<p style="font-size:{size};line-height:30px;font-family:{stack};color:{BLACK};'
        f'font-weight:bold;text-align:center;margin:0;padding:20px 60px 30px;">{text}</p>'
    )


def body_copy(text: str, lineage: Lineage = "whyte", align: str = "center") -> str:
    stack = _font_stack(lineage)
    lh = "28px" if lineage == "whyte" else "22px"
    fs = "20px" if lineage == "whyte" else "16px"
    pad = "0 60px 20px" if lineage == "whyte" else "0 60px 24px"
    return (
        f'<p style="font-size:{fs};line-height:{lh};font-family:{stack};color:{BLACK};'
        f'text-align:{align};margin:0;padding:{pad};">{text}</p>'
    )


def inline_link(text: str, url: str) -> str:
    return (
        f'<a href="{url}" style="color:{PURPLE};font-weight:bold;text-decoration:none;">{text}</a>'
    )


def cta_button(text: str, url: str, style: CtaStyle = "purple", lineage: Lineage = "whyte") -> str:
    stack = _font_stack(lineage)
    if style == "purple":
        cell = (
            f'background-color:{PURPLE};border:5px solid {PURPLE};border-radius:8px;'
            f'font-family:{stack};font-size:20px;font-weight:bold;'
        )
        link_color = WHITE
    elif style == "outline":
        cell = (
            f'background-color:{WHITE};border:5px solid {BLACK};border-radius:8px;'
            f'font-family:{stack};font-size:20px;font-weight:bold;'
        )
        link_color = BLACK
    else:
        cell = (
            f'background-color:{BLACK};border:3px solid {BLACK};border-radius:8px;'
            f'font-family:{stack};font-size:18px;'
        )
        link_color = WHITE

    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" align="center" style="background-color:{WHITE};">
<tr><td style="padding:30px 0 60px;" align="center">
  <table role="presentation" cellpadding="0" cellspacing="0" align="center">
  <tr><td align="center" style="{cell}">
    <a href="{url}" style="padding:12px 27px;color:{link_color};text-decoration:none;display:block;">{text}</a>
  </td></tr></table>
</td></tr></table>"""


def image_left_row(
    img_url: str,
    img_alt: str,
    title: str,
    body: str,
    link_text: str,
    link_url: str,
    img_link: str = "#",
) -> str:
    arrow = link_text if "→" in link_text else f"{link_text} →"
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:0 10px 50px;">
<tr>
  <td valign="top" width="150" style="padding:0;">
    <a href="{img_link}"><img src="{img_url}" width="150" alt="{img_alt}" style="width:150px;max-width:150px;border:0;" /></a>
  </td>
  <td valign="middle" style="padding:0 60px 0 40px;font-family:{WHYTE_STACK};">
    <p style="font-size:22px;line-height:28px;font-weight:bold;color:{BLACK};margin:0;">{title}</p>
    <p style="font-size:18px;line-height:22px;color:{BLACK};margin:10px 0 0;">{body}</p>
    <p style="font-size:18px;line-height:21px;margin:10px 0 0;">
      <a href="{link_url}" style="color:{PURPLE};font-weight:bold;text-decoration:none;">{arrow}</a>
    </p>
  </td>
</tr></table>"""


def bulleted_resources(items: list[tuple[str, str, str]]) -> str:
    """Each item: (lead_in, link_text, url) e.g. ('Get started with comments:', 'Learn how', url)."""
    rows = ""
    for lead, link_text, url in items:
        rows += (
            f'<p style="font-size:20px;line-height:28px;font-family:{WHYTE_STACK};'
            f'color:{BLACK};margin:0 0 12px;padding:0 60px;">'
            f'{lead} <a href="{url}" style="color:#699BF7;text-decoration:none;">{link_text}</a></p>'
        )
    return rows


def icon_list_row(icon_url: str, icon_alt: str, title: str, body: str) -> str:
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:0 60px 24px;">
<tr>
  <td valign="top" width="80" style="padding-right:16px;">
    <img src="{icon_url}" width="80" alt="{icon_alt}" style="width:80px;border:0;" />
  </td>
  <td valign="top" style="font-family:{INTER_STACK};">
    <p style="font-size:22px;line-height:28px;font-weight:600;color:{BLACK};margin:0;">{title}</p>
    <p class="fs-body" style="font-size:16px;line-height:22px;color:{BLACK};margin:8px 0 0;">{body}</p>
  </td>
</tr></table>"""


def two_column_grid(
    left_img: str,
    left_alt: str,
    left_title: str,
    left_body: str,
    left_link: str,
    right_img: str,
    right_alt: str,
    right_title: str,
    right_body: str,
    right_link: str,
) -> str:
    col = lambda img, alt, title, body, link: f"""
    <td valign="top" width="289" class="tflex" style="padding:0 8px 24px;">
      <img src="{img}" width="289" alt="{alt}" style="width:100%;max-width:289px;border-radius:8px;border:0;" />
      <p style="font-size:22px;line-height:28px;font-weight:600;font-family:{INTER_STACK};color:{BLACK};margin:16px 0 8px;">{title}</p>
      <p style="font-size:16px;line-height:22px;font-family:{INTER_STACK};color:{BLACK};margin:0 0 12px;">{body}</p>
      <a href="{link}" style="color:{PURPLE};font-weight:bold;text-decoration:underline;font-size:16px;">Learn more →</a>
    </td>"""
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:0 52px;">
<tr>{col(left_img, left_alt, left_title, left_body, left_link)}{col(right_img, right_alt, right_title, right_body, right_link)}</tr>
</table>"""


def newsletter_card_open() -> str:
    return f"""<table role="presentation" width="{MAX_WIDTH}" align="center" style="max-width:{MAX_WIDTH}px;margin:0 auto;background:{WHITE};border-radius:24px;" cellpadding="0" cellspacing="0">
<tr><td>"""


def newsletter_card_close() -> str:
    return "</td></tr></table>"


def footer(lineage: Lineage = "whyte") -> str:
    stack = _font_stack(lineage)
    social_cells = ""
    for i, (name, url, icon) in enumerate(SOCIAL_ICONS):
        if i > 0:
            social_cells += '<td width="30" style="font-size:1px;line-height:1px;"></td>'
        social_cells += (
            f'<td class="active-i" style="line-height:1px;font-size:1px;">'
            f'<a href="{url}"><img src="{icon}" width="30" alt="{name}" style="width:30px;border:0;" /></a></td>'
        )

    return f"""<table role="presentation" width="{MAX_WIDTH}" align="center" style="max-width:{MAX_WIDTH}px;margin:0 auto;border-top:1px solid #DEDEDE;background:{WHITE};" cellpadding="0" cellspacing="0">
<tr><td style="padding:35px 10px 46px;" align="center">
  <table role="presentation" width="410" align="center" style="max-width:410px;margin:0 auto;" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:15px 0 32px;font-size:14px;line-height:20px;font-family:{stack};color:{MUTED};">
    Figma is a design platform for teams who build products together. Born on the Web, Figma helps the entire product team create, test, and ship better designs, faster.
  </td></tr>
  <tr><td style="padding:0 0 32px;"><table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr>{social_cells}</tr></table></td></tr>
  <tr><td align="center" style="font-size:12px;line-height:18px;font-family:{stack};color:{FOOTER_MUTED};padding-bottom:8px;">
    Figma, Inc. · 760 Market St · San Francisco, CA 94102
  </td></tr>
  <tr><td align="center" style="font-size:12px;line-height:18px;font-family:{stack};color:{FOOTER_MUTED};">
    <a href="*|UNSUBSCRIBE|*" style="color:{FOOTER_MUTED};text-decoration:underline;">Unsubscribe</a>
  </td></tr>
  </table>
</td></tr></table>"""


def wrap_document(
    title: str,
    preview_text: str,
    body_content: str,
    lineage: Lineage = "whyte",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<title>{title}</title>
{_head_css(lineage)}
</head>
<body class="darkmode" style="background:{WHITE};margin:0;padding:0;-webkit-text-size-adjust:100%;">
{preview_text_div(preview_text)}
<table role="presentation" width="100%" style="background:{WHITE};min-width:320px;" cellpadding="0" cellspacing="0">
<tr><td>
{body_content}
</td></tr></table>
</body>
</html>"""
