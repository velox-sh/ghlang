from pathlib import Path

import matplotlib.pyplot as plt

from ..logging import logger
from .constants import HIDE_THRESHOLD
from .constants import PIE_FIGSIZE
from .constants import PIE_LEGEND_FONTSIZE
from .constants import PIE_LEGEND_TITLE_FONTSIZE
from .constants import PIE_PCT_FONTSIZE
from .constants import PIE_TITLE_FONTSIZE
from .constants import PIE_TITLE_PAD
from .utils import get_theme
from .utils import save_matplotlib_chart


def generate_pie(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
    **_kwargs: object,
) -> None:
    """Generate a pie chart showing language distribution"""
    title = title if title else "Language Distribution"
    logger.debug(f"Generating pie chart with {len(language_stats)} languages...")

    theme_colors = get_theme(theme)
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    labels = [lang for lang, _ in items]
    sizes = [count for _, count in items]
    fallback = theme_colors["fallback"]
    chart_colors = [colors.get(lang, fallback) for lang in labels]

    fig, ax = plt.subplots(figsize=PIE_FIGSIZE)
    fig.patch.set_facecolor(theme_colors["background"])
    ax.set_facecolor(theme_colors["background"])

    wedges, _, autotexts = ax.pie(  # type: ignore[misc]
        sizes,
        colors=chart_colors,
        autopct=lambda p: f"{p:.1f}%" if p >= HIDE_THRESHOLD else "",
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

    save_matplotlib_chart(output, theme_colors["background"])
    logger.success(f"Saved pie chart to {output}")
