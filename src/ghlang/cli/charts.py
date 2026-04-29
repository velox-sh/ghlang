from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from ghlang import log
from ghlang import styles
from ghlang.net import linguist
from ghlang.styles import constants as style_constants


if TYPE_CHECKING:
    from ghlang.config import Config


def get_chart_title(items: list | None, custom_title: str | None, source: str) -> str:
    """Generate a chart title from the analyzed items or a custom override.

    Parameters
    ----------
    items : list | None
        Repos (str) or paths (Path) being analyzed.
    custom_title : str | None
        Explicit title that takes priority when set.
    source : str
        Label for the data source (``"GitHub"`` or ``"Local"``).

    Returns
    -------
    str
        Human-readable chart title.
    """
    if custom_title:
        return custom_title

    if items and len(items) == 1:
        if source == "GitHub":
            return f"GitHub: {items[0]}"

        resolved = items[0].expanduser().resolve()
        return f"Local: {resolved.name}"

    if items:
        item_type = "repos" if source == "GitHub" else "paths"
        return f"{source}: {len(items)} {item_type}"

    return f"{source} Language Stats"


def generate_charts(
    language_stats: dict[str, int],
    cfg: Config,
    title: str | None = None,
    output: Path | None = None,
    style: str = "pixel",
    top_n: int = style_constants.TOP_N,
    save_json: bool = False,
) -> None:
    """Load language colors and render a chart in the requested style.

    Parameters
    ----------
    language_stats : dict[str, int]
        Language name to count mapping.
    cfg : Config
        Active configuration (provides output_dir and theme).
    title : str | None
        Chart title. Auto-generated when *None*.
    output : Path | None
        Custom output filename or path.
    style : str
        Chart style name (pixel, pie, bar).
    top_n : int
        Maximum number of languages shown before grouping into "Other".
    save_json : bool
        Also persist the GitHub color map as JSON.

    Raises
    ------
    typer.Exit
        If the requested style is unknown.
    """
    style_fn = styles.get_style_registry().get(style)
    if style_fn is None:
        log.logger.error(f"Unknown style '{style}', available: {', '.join(styles.STYLES)}")
        raise typer.Exit(1)

    with log.logger.progress() as progress:
        task = progress.add_task("Generating chart", total=2)

        progress.update(task, description="Loading language colors...")
        colors_file = cfg.output_dir / "github_colors.json" if save_json else None
        colors = linguist.load_github_colors(output_file=colors_file)
        progress.advance(task)

        if not colors:
            log.logger.warning("Couldn't load GitHub colors, charts will be gray")
            colors = {}

        # all output is PNG for now (SVG support TODO)
        if output:
            if output.is_absolute():
                parent = output.parent
            elif str(output.parent) != ".":
                parent = cfg.output_dir / output.parent
            else:
                parent = cfg.output_dir
            stem = output.stem
        else:
            parent = cfg.output_dir
            stem = "language"

        chart_output = parent / f"{stem}_{style}.png"

        progress.update(task, description=f"Generating {style} chart...")
        style_fn(language_stats, colors, chart_output, title, cfg.theme, top_n=top_n)
        progress.advance(task)


def get_output_path(output_dir: Path, filename: str, save_json: bool, stdout: bool) -> Path | None:
    """Return a JSON output path, or None when saving is disabled.

    Parameters
    ----------
    output_dir : Path
        Base directory for output files.
    filename : str
        JSON filename to use.
    save_json : bool
        Whether JSON saving is enabled.
    stdout : bool
        Whether output is going to stdout (suppresses file writes).

    Returns
    -------
    Path | None
        Full path when saving is enabled, otherwise *None*.
    """
    if not save_json or stdout:
        return None
    return output_dir / filename
