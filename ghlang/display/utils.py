import io
import json
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image
from PIL import ImageDraw
import requests
import yaml

from ..config import get_config_path
from ..constants import LINGUIST_URL
from ..constants import REQUEST_TIMEOUT
from ..logging import logger
from ..static.lang_mapping import TOKOUNT_TO_LINGUIST
from ..static.themes import THEMES
from ..themes import load_all_themes
from .constants import HIDE_THRESHOLD
from .constants import PNG_DPI
from .constants import ROUNDED_CORNER_RADIUS


def build_display_segments(
    language_stats: dict[str, int],
    top_n: int,
) -> list[tuple[str, float]]:
    """Build (name, pct) segments applying top_n + HIDE_THRESHOLD, remainder into 'Other'"""
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    shown: list[tuple[str, float]] = []
    others_pct = 0.0

    for i, (name, count) in enumerate(items):
        pct = count / total * 100
        if i < top_n and pct >= HIDE_THRESHOLD:
            shown.append((name, pct))
        else:
            others_pct += pct

    if others_pct > 0:
        shown.append(("Other", round(others_pct, 1)))

    return shown


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert #RRGGBB hex string to (R, G, B) tuple"""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _normalize_language(lang: str) -> str:
    if lang in TOKOUNT_TO_LINGUIST:
        mapped = TOKOUNT_TO_LINGUIST[lang]
        return mapped if mapped is not None else lang
    return lang


def normalize_language_stats(stats: dict[str, int]) -> dict[str, int]:
    """Normalize language names and merge duplicates"""
    normalized: dict[str, int] = {}
    for lang, count in stats.items():
        norm_lang = _normalize_language(lang)
        normalized[norm_lang] = normalized.get(norm_lang, 0) + count
    return normalized


def load_github_colors(output_file: Path | None = None) -> dict[str, str]:
    """Fetch GitHub's language colors from linguist YAML"""
    logger.info("Grabbing language colors from GitHub")

    try:
        r = requests.get(LINGUIST_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()

        data = yaml.safe_load(r.text)
        colors: dict[str, str] = {}

        for lang, props in data.items():
            if isinstance(props, dict) and "color" in props:
                colors[lang] = props["color"]
        logger.success(f"Loaded {len(colors)} language colors")

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w") as f:
                json.dump(colors, f, indent=2)
            logger.debug(f"Saved color data to {output_file}")

        return colors

    except Exception as e:
        logger.warning(f"Couldn't load GitHub colors: {e}")
        return {}


def get_theme(theme: str) -> dict[str, str]:
    """Get theme colors (built-in + remote + custom), defaulting to light if invalid"""
    config_dir = get_config_path().parent

    all_themes = load_all_themes(config_dir)
    if theme not in all_themes:
        logger.warning(f"No '{theme}' theme exists, using light instead")
        return THEMES["light"]

    return all_themes[theme]


def add_rounded_corners(img: Image.Image, radius: int = ROUNDED_CORNER_RADIUS) -> Image.Image:
    """Add rounded corners to an image"""
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def save_matplotlib_chart(output: Path, background_color: str) -> None:
    """Save matplotlib figure to PNG with rounded corners"""
    # TODO: re-enable SVG support once PNG pipeline is stable
    output.parent.mkdir(parents=True, exist_ok=True)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=PNG_DPI, bbox_inches="tight", facecolor=background_color)
    plt.close()
    buf.seek(0)

    img = Image.open(buf)

    rounded = add_rounded_corners(img)
    rounded.save(output)
