from __future__ import annotations

from collections.abc import Iterator
import contextlib
from contextlib import contextmanager
import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from ghlang.config import get_config_path
from ghlang.config import load_config
from ghlang.display import STYLES
from ghlang.display.constants import TOP_N
from ghlang.logging import logger
from ghlang.static.themes import THEMES


if TYPE_CHECKING:
    from ghlang.config import Config


def get_config_dir() -> Path:
    """Get the config directory path"""
    return get_config_path().parent


def get_active_theme() -> str:
    """Get the currently active theme name"""
    try:
        return load_config(require_token=False).theme
    except Exception:
        return "light"


def load_themes_by_source(
    config_dir: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Return (built-in, remote, custom) theme dicts loaded independently"""
    built_in: dict[str, dict[str, str]] = dict(THEMES)

    remote: dict[str, dict[str, str]] = {}
    remote_path = config_dir / "themes.json"
    if remote_path.exists():
        with contextlib.suppress(Exception):
            remote = json.loads(remote_path.read_text())

    custom: dict[str, dict[str, str]] = {}
    custom_path = config_dir / "custom_themes.json"
    if custom_path.exists():
        with contextlib.suppress(Exception):
            custom = json.loads(custom_path.read_text())

    return built_in, remote, custom


def format_autocomplete(incomplete: str) -> list[str]:
    """Callback for output formats"""
    return [f for f in ["png", "svg"] if f.startswith(incomplete)]


def themes_autocomplete(incomplete: str) -> list[str]:
    """Callback for theme names"""
    themes = list(THEMES.keys())

    config_path = get_config_path()
    remote_path = config_path.parent / "themes.json"
    if remote_path.exists():
        try:
            with remote_path.open() as f:
                remote = json.load(f)
            themes.extend(remote.keys())

        except Exception:
            pass

    return [t for t in themes if t.startswith(incomplete)]


def styles_autocomplete(incomplete: str) -> list[str]:
    """Callback for chart styles"""
    return [s for s in STYLES if s.startswith(incomplete)]


def get_chart_title(items: list | None, custom_title: str | None, source: str) -> str:
    """Generate chart title based on items or custom title"""
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
    top_n: int = TOP_N,
    save_json: bool = False,
) -> None:
    """Load colors and generate a chart in the requested style"""
    from ghlang.display import get_style_registry  # noqa: PLC0415
    from ghlang.display.utils import load_github_colors  # noqa: PLC0415

    style_fn = get_style_registry().get(style)
    if style_fn is None:
        logger.error(f"Unknown style '{style}', available: {', '.join(STYLES)}")
        raise typer.Exit(1)

    with logger.progress() as progress:
        task = progress.add_task("Generating chart", total=2)

        progress.update(task, description="Loading language colors...")
        colors_file = cfg.output_dir / "github_colors.json" if save_json else None
        colors = load_github_colors(output_file=colors_file)
        progress.advance(task)

        if not colors:
            logger.warning("Couldn't load GitHub colors, charts will be gray")
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


def save_json_stats(language_stats: dict[str, int], output_dir: Path) -> None:
    """Save language stats as JSON file"""
    stats_file = output_dir / "language_stats.json"

    with stats_file.open("w") as f:
        json.dump(language_stats, f, indent=2)

    logger.success(f"Saved stats to {stats_file}")


def get_output_path(output_dir: Path, filename: str, save_json: bool, stdout: bool) -> Path | None:
    """Get output path for JSON files or None if not saving"""
    if not save_json or stdout:
        return None
    return output_dir / filename


def setup_cli_environment(
    config_path: Path | None,
    output_dir: Path | None,
    verbose: bool,
    theme: str | None,
    stdout: bool,
    quiet: bool,
    require_token: bool,
) -> tuple[Config, bool, bool]:
    """Common CLI setup tasks"""
    if stdout:
        quiet = True
        json_only = True
    else:
        json_only = False

    logger.configure(verbose, quiet=quiet)

    cli_overrides = {
        "output_dir": output_dir,
        "verbose": verbose or None,
        "theme": theme,
    }

    cfg = load_config(
        config_path=config_path,
        cli_overrides=cli_overrides,
        require_token=require_token,
    )

    logger.configure(cfg.verbose, quiet=quiet)

    if not stdout:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving to {cfg.output_dir}")

    return cfg, quiet, json_only


@contextmanager
def handle_cli_errors() -> Iterator[None]:
    """Context manager for handling CLI exceptions"""
    try:
        yield

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception(f"Something went wrong: {e}")
        raise typer.Exit(1)
