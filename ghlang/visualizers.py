import io
import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from PIL import Image
from PIL import ImageDraw
import requests
import yaml

from .config import get_config_path
from .constants import BAR_FIGSIZE
from .constants import BAR_HEIGHT
from .constants import BAR_LABEL_FONTSIZE
from .constants import BAR_LEGEND_FONTSIZE
from .constants import BAR_LEGEND_NCOL
from .constants import BAR_MIN_LABEL_WIDTH
from .constants import BAR_TITLE_FONTSIZE
from .constants import BAR_TITLE_PAD
from .constants import LINGUIST_LANGUAGES_URL
from .constants import PIE_FIGSIZE
from .constants import PIE_LEGEND_FONTSIZE
from .constants import PIE_LEGEND_TITLE_FONTSIZE
from .constants import PIE_MIN_PERCENTAGE
from .constants import PIE_PCT_FONTSIZE
from .constants import PIE_TITLE_FONTSIZE
from .constants import PIE_TITLE_PAD
from .constants import PNG_DPI
from .constants import REQUEST_TIMEOUT
from .constants import ROUNDED_CORNER_RADIUS
from .logging import logger
from .static.lang_mapping import TOKEI_TO_LINGUIST
from .static.themes import THEMES
from .themes import load_all_themes


def _normalize_language(lang: str) -> str:
    """Normalize tokount language name to GitHub linguist name"""
    if lang in TOKEI_TO_LINGUIST:
        mapped = TOKEI_TO_LINGUIST[lang]
        return mapped if mapped is not None else lang
    return lang


def normalize_language_stats(stats: dict[str, int]) -> dict[str, int]:
    """Normalize language names and merge duplicates"""
    normalized: dict[str, int] = {}

    for lang, count in stats.items():
        norm_lang = _normalize_language(lang)

        normalized[norm_lang] = normalized.get(norm_lang, 0) + count

    return normalized


def _add_rounded_corners(img: Image.Image, radius: int = ROUNDED_CORNER_RADIUS) -> Image.Image:
    """Add rounded corners to an image"""
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _get_theme(theme: str) -> dict[str, str]:
    """Get theme colors (built-in + remote + custom), defaulting to light if invalid"""
    config_dir = get_config_path().parent
    all_themes = load_all_themes(config_dir)

    if theme not in all_themes:
        logger.warning(f"No '{theme}' theme exists, using light instead")
        return THEMES["light"]

    return all_themes[theme]


def _save_chart(output: Path, background_color: str) -> None:
    """Save chart to file (also apply rounded corners)"""
    output.parent.mkdir(parents=True, exist_ok=True)
    is_svg = output.suffix.lower() == ".svg"

    if is_svg:
        plt.savefig(output, format="svg", bbox_inches="tight", facecolor=background_color)
        plt.close()
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=PNG_DPI, bbox_inches="tight", facecolor=background_color)
        plt.close()
        buf.seek(0)
        img = Image.open(buf)
        rounded = _add_rounded_corners(img)
        rounded.save(output)


def load_github_colors(output_file: Path | None = None) -> dict[str, str]:
    """Fetch GitHub's language colors from linguist YAML"""
    logger.info("Grabbing language colors from GitHub")

    try:
        r = requests.get(LINGUIST_LANGUAGES_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = yaml.safe_load(r.text)
        colors = {}

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


def generate_pie(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
) -> None:
    """Generate a pie chart showing language distribution"""
    title = title if title else "Language Distribution"
    logger.debug(f"Generating pie chart with {len(language_stats)} languages...")

    theme_colors = _get_theme(theme)
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    labels = [lang for lang, _ in items]
    sizes = [count for _, count in items]
    fallback = theme_colors["fallback"]
    chart_colors = [colors.get(lang, fallback) for lang in labels]

    fig, ax = plt.subplots(figsize=PIE_FIGSIZE)
    fig.patch.set_facecolor(theme_colors["background"])
    ax.set_facecolor(theme_colors["background"])

    wedges, texts, autotexts = ax.pie(  # type: ignore[misc]
        sizes,
        colors=chart_colors,
        autopct=lambda p: f"{p:.1f}%" if p >= PIE_MIN_PERCENTAGE else "",
        startangle=90,
        pctdistance=0.85,
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(PIE_PCT_FONTSIZE)
        autotext.set_weight("bold")  # type: ignore[union-attr]

    legend_labels = [f"{lang} ({count / total * 100:.1f}%)" for lang, count in items]
    legend = ax.legend(
        wedges,
        legend_labels,
        title="Languages",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=PIE_LEGEND_FONTSIZE,
        title_fontsize=PIE_LEGEND_TITLE_FONTSIZE,
    )

    legend.get_frame().set_facecolor(theme_colors["legend_bg"])
    legend.get_frame().set_edgecolor(theme_colors["legend_bg"])
    legend.get_title().set_color(theme_colors["text"])
    for text in legend.get_texts():
        text.set_color(theme_colors["secondary"])

    ax.set_title(
        title,
        fontsize=PIE_TITLE_FONTSIZE,
        weight="bold",
        color=theme_colors["text"],
        pad=PIE_TITLE_PAD,
    )

    _save_chart(output, theme_colors["background"])
    logger.success(f"Saved pie chart to {output}")


def generate_bar(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    top_n: int = 5,
    title: str | None = None,
    theme: str = "light",
) -> None:
    """Generate a horizontal segmented bar chart showing top N languages"""
    title = title if title else f"Top {top_n} Languages"
    logger.debug(f"Generating segmented bar chart (top {top_n} languages)...")

    theme_colors = _get_theme(theme)
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    top = items[:top_n]
    other_count = total - sum(count for _, count in top)

    segments = top + ([("Other", other_count)] if other_count > 0 else [])

    fig, ax = plt.subplots(figsize=BAR_FIGSIZE)
    fig.patch.set_facecolor(theme_colors["background"])
    ax.set_facecolor(theme_colors["background"])

    left = 0.0
    fallback = theme_colors["fallback"]

    for lang, count in segments:
        width = count / total
        color = colors.get(lang, fallback)

        ax.barh(
            0,
            width,
            BAR_HEIGHT,
            left=left,
            color=color,
            edgecolor=theme_colors["background"],
            linewidth=2,
        )

        if width >= BAR_MIN_LABEL_WIDTH:
            ax.text(
                left + width / 2,
                0,
                f"{width * 100:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=BAR_LABEL_FONTSIZE,
                weight="bold",
            )

        left += width

    legend_elements = [
        mpatches.Patch(
            color=colors.get(lang, fallback),
            label=f"{lang} ({count / total * 100:.1f}%)",
        )
        for lang, count in segments
    ]

    legend = ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.05),
        ncol=min(len(segments), BAR_LEGEND_NCOL),
        frameon=False,
        fontsize=BAR_LEGEND_FONTSIZE,
    )
    for text in legend.get_texts():
        text.set_color(theme_colors["secondary"])

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")

    ax.set_title(
        title,
        fontsize=BAR_TITLE_FONTSIZE,
        weight="bold",
        color=theme_colors["text"],
        pad=BAR_TITLE_PAD,
    )

    _save_chart(output, theme_colors["background"])
    logger.success(f"Saved segmented bar chart to {output}")
