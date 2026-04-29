from pathlib import Path
from typing import cast

from matplotlib.patches import Wedge
import matplotlib.pyplot as plt
from matplotlib.text import Text

from ghlang import log
from ghlang import themes

from . import constants
from . import utils


def generate_pie(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
    **_kwargs: object,
) -> None:
    """Generate a pie chart showing language distribution.

    Parameters
    ----------
    language_stats : dict[str, int]
        Language name to count mapping.
    colors : dict[str, str]
        Language name to hex color mapping.
    output : Path
        Destination PNG file path.
    title : str | None
        Chart title. Defaults to ``"Language Distribution"``.
    theme : str
        Theme name for background, text, and legend colors.
    **_kwargs : object
        Ignored extra keyword arguments for signature compatibility.
    """
    title = title if title else "Language Distribution"
    log.logger.debug(f"Generating pie chart with {len(language_stats)} languages...")

    theme_colors = themes.get_theme(theme)
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    labels = [lang for lang, _ in items]
    sizes = [count for _, count in items]
    fallback = theme_colors["fallback"]
    chart_colors = [colors.get(lang, fallback) for lang in labels]

    fig, ax = plt.subplots(figsize=constants.PIE_FIGSIZE)
    fig.patch.set_facecolor(theme_colors["background"])
    ax.set_facecolor(theme_colors["background"])

    # autopct triggers 3-tuple return
    # stubs pick the 2-tuple overload
    pie_result = cast(
        tuple[list[Wedge], list[Text], list[Text]],
        ax.pie(
            sizes,
            colors=chart_colors,
            autopct=lambda p: f"{p:.1f}%" if p >= constants.PIE_THRESHOLD else "",
            startangle=90,
            pctdistance=0.85,
        ),
    )
    wedges, _, autotexts = pie_result

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(constants.PIE_PCT_FONTSIZE)
        autotext.set_fontweight("bold")

    legend_labels = [f"{lang} ({count / total * 100:.1f}%)" for lang, count in items]
    legend = ax.legend(
        wedges,
        legend_labels,
        title="Languages",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=constants.PIE_LEGEND_FONTSIZE,
        title_fontsize=constants.PIE_LEGEND_TITLE_FONTSIZE,
    )

    legend.get_frame().set_facecolor(theme_colors["legend_bg"])
    legend.get_frame().set_edgecolor(theme_colors["legend_bg"])
    legend.get_title().set_color(theme_colors["text"])
    for text in legend.get_texts():
        text.set_color(theme_colors["secondary"])

    ax.set_title(
        title,
        fontsize=constants.PIE_TITLE_FONTSIZE,
        weight="bold",
        color=theme_colors["text"],
        pad=constants.PIE_TITLE_PAD,
    )

    utils.save_matplotlib_chart(output, theme_colors["background"])
    log.logger.success(f"Saved pie chart to {output}")
