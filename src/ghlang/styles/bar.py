from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from ghlang import log
from ghlang import themes

from . import constants
from . import utils


def generate_bar(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
    top_n: int = constants.TOP_N,
) -> None:
    """Generate a horizontal segmented bar chart showing top N languages.

    Parameters
    ----------
    language_stats : dict[str, int]
        Language name to count mapping.
    colors : dict[str, str]
        Language name to hex color mapping.
    output : Path
        Destination PNG file path.
    title : str | None
        Chart title. Defaults to ``"Top {top_n} Languages"``.
    theme : str
        Theme name for background, text, and legend colors.
    top_n : int
        Maximum number of language segments before grouping into "Other".
    """
    title = title if title else f"Top {top_n} Languages"
    log.logger.debug(f"Generating segmented bar chart (top {top_n} languages)...")

    theme_colors = themes.get_theme(theme)
    segments = utils.build_display_segments(language_stats, top_n)

    fig, ax = plt.subplots(figsize=constants.BAR_FIGSIZE)
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
            constants.BAR_HEIGHT,
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
            fontsize=constants.BAR_LABEL_FONTSIZE,
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
        ncol=min(len(segments), constants.BAR_LEGEND_NCOL),
        frameon=False,
        fontsize=constants.BAR_LEGEND_FONTSIZE,
    )
    for text in legend.get_texts():
        text.set_color(theme_colors["secondary"])

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")

    ax.set_title(
        title,
        fontsize=constants.BAR_TITLE_FONTSIZE,
        weight="bold",
        color=theme_colors["text"],
        pad=constants.BAR_TITLE_PAD,
    )

    utils.save_matplotlib_chart(output, theme_colors["background"])
    log.logger.success(f"Saved segmented bar chart to {output}")
