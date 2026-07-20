"""
Asset Pool — Rotating visual assets for email templates.

Uses deterministic hourly rotation so the same brief type gets different
hero images, row images, and icons across runs without randomness issues.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

# ── Hero images (width 650) — used for product launch, event, educational, re-engagement ──
HERO_POOL = [
    "https://static.figma.com/uploads/efb8b874cf81705346aeaa7d4d5d65ca23a9836e",
    "https://static.figma.com/uploads/09d331398f2b57bee77b7339209ec2cd4190d6bb",
    "https://static.figma.com/uploads/07ef022da08e21990bfcfed3d77bfe6dbb4993e6",
    "https://static.figma.com/uploads/03ac25c18fff770974c2f56dbf6416ea90c5eb5e",
]

# ── Row feature images (width 150) — used in image_left_row and icon_list_row ──
ROW_POOL = [
    "https://static.figma.com/uploads/ebda29ac2a7ddefa6f23c64e6c0514c8e9029ba4",
    "https://static.figma.com/uploads/c945b793ff6a1f4d7fc5e3f6cb28967aa5a3eb5e",
    "https://static.figma.com/uploads/7447a4e177ed113a92315a3f2f30c2acf505d0d2",
    "https://static.figma.com/uploads/726c6143248e475d620cde1e8da7c39a1e0ce76e",
    "https://static.figma.com/uploads/60d0569fcaf314946b524c33e5f7ca8729d3bba2",
    "https://static.figma.com/uploads/4de5c04f4bc5b018f26d2a2f31ec564ffb944a62",
    "https://static.figma.com/uploads/072fa9ed8750ea7948505c1424345fbc39cbb6b4",
]

# ── Feature update card hero (width 650) — used for newsletter-style feature updates ──
FEATURE_HERO_POOL = [
    "https://static.figma.com/uploads/09d331398f2b57bee77b7339209ec2cd4190d6bb",
    "https://static.figma.com/uploads/07ef022da08e21990bfcfed3d77bfe6dbb4993e6",
    "https://static.figma.com/uploads/03ac25c18fff770974c2f56dbf6416ea90c5eb5e",
    "https://static.figma.com/uploads/efb8b874cf81705346aeaa7d4d5d65ca23a9836e",
]

# ── Feature update grid images (width 600) — used in two_column_grid ──
FEATURE_GRID_POOL = [
    "https://static.figma.com/uploads/7cbabd510cbe2f41dc9ca3a027f058d08ea71223",
    "https://static.figma.com/uploads/4d0e1106896074cfeb3c801076ca9ed71ac92fe5",
    "https://static.figma.com/uploads/2275d74dda845c4d5516ceef1a24e95f71559232",
]

# ── Large icon images (width 80) — used in icon_list_row ──
ICON_POOL = [
    "https://static.figma.com/uploads/4e759a031b37029f4808810146b59b585b41e9f2",
    "https://static.figma.com/uploads/a6883e0b3d2b5db3978e22b5c8e9da7ebfd45356",
    "https://static.figma.com/uploads/9c0846315970f4fc09d9e93a742b1666a7a766b4",
    "https://static.figma.com/uploads/252065a327c097ab6f47b8e41f1cdc9a8044ed83",
]

# ── Medium secondary images (width 65-289) — fallbacks for grid/secondary slots ──
MEDIUM_POOL = [
    "https://static.figma.com/uploads/4d0e1106896074cfeb3c801076ca9ed71ac92fe5",
    "https://static.figma.com/uploads/2275d74dda845c4d5516ceef1a24e95f71559232",
    "https://static.figma.com/uploads/fd222b164c8e5d3814c3cfb3476d3a32ed159390",
    "https://static.figma.com/uploads/c2698d9a70dc8fe5ec7bc50d0141f831bf2ab2df",
]


def _hourly_seed(extra: str = "") -> str:
    """Deterministic seed that rotates hourly. Same seed for 1-hour window."""
    hour = datetime.now().strftime("%Y%m%d%H")
    return f"{hour}:{extra}"


def _pick(pool: list[str], index: int, seed: str = "") -> str:
    """Pick from pool using deterministic index + hourly seed rotation."""
    raw = hashlib.md5(f"{seed}:{index}:pool".encode()).hexdigest()
    idx = int(raw, 16) % len(pool)
    return pool[idx]


def hero_image(seed: str = "") -> str:
    """Hero image for product launch, event, educational, re-engagement."""
    return _pick(HERO_POOL, 1, _hourly_seed(seed))


def row_image(index: int, seed: str = "") -> str:
    """Row feature image for image_left_row. Vary by index for multiple rows."""
    return _pick(ROW_POOL, index, _hourly_seed(seed))


def feature_hero(seed: str = "") -> str:
    """Card hero image for feature update / newsletter templates."""
    return _pick(FEATURE_HERO_POOL, 5, _hourly_seed(seed))


def feature_grid(index: int, seed: str = "") -> str:
    """Grid image for two_column_grid. Vary by index for left/right."""
    return _pick(FEATURE_GRID_POOL, index + 10, _hourly_seed(seed))


def icon_image(index: int, seed: str = "") -> str:
    """Large icon for icon_list_row."""
    return _pick(ICON_POOL, index + 20, _hourly_seed(seed))


def secondary_image(index: int, seed: str = "") -> str:
    """Secondary/medium image fallback."""
    return _pick(MEDIUM_POOL, index + 30, _hourly_seed(seed))
