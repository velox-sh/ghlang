from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from ..logging import logger
from .constants import BAR_FIGSIZE
from .constants import BAR_HEIGHT
from .constants import BAR_LABEL_FONTSIZE
from .constants import BAR_LEGEND_FONTSIZE
from .constants import BAR_LEGEND_NCOL
from .constants import BAR_TITLE_FONTSIZE
from .constants import BAR_TITLE_PAD
from .constants import TOP_N
from .utils import build_display_segments
from .utils import get_theme
from .utils import save_matplotlib_chart


def generate_bar(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
    top_n: int = TOP_N,
) -> None:
    """Generate a horizontal segmented bar chart showing top N languages"""
    title = title if title else f"Top {top_n} Languages"
    logger.debug(f"Generating segmented bar chart (top {top_n} languages)...")

    theme_colors = get_theme(theme)
    segments = build_display_segments(language_stats, top_n)

    fig, ax = plt.subplots(figsize=BAR_FIGSIZE)
    fig.patch.set_facecolor(theme_colors["background"])
    ax.set_facecolor(theme_colors["background"])

    left = 0.0
    fallback = theme_colors["fallback"]

    for name, pct in segments:
        width = pct / 100
        color = colors.get(name, fallback)

        ax.barh(
            0,
            width,
            BAR_HEIGHT,
            left=left,
            color=color,
            edgecolor=theme_colors["background"],
            linewidth=2,
        )

        ax.text(
            left + width / 2,
            0,
            f"{pct:.1f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=BAR_LABEL_FONTSIZE,
            weight="bold",
        )

        left += width

    legend_elements = [
        mpatches.Patch(
            color=colors.get(name, fallback),
            label=f"{name} ({pct:.1f}%)",
        )
        for name, pct in segments
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

    save_matplotlib_chart(output, theme_colors["background"])
    logger.success(f"Saved segmented bar chart to {output}")
