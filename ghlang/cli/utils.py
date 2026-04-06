from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from ghlang import config
from ghlang import log
from ghlang import styles
from ghlang.static import themes as static_themes


if TYPE_CHECKING:
    from ghlang.config import Config


def _format_autocomplete(incomplete: str) -> list[str]:
    """Return matching output format completions"""
    return [f for f in ["png", "svg"] if f.startswith(incomplete)]


def themes_autocomplete(incomplete: str) -> list[str]:
    """Return matching theme name completions."""
    themes = list(static_themes.THEMES.keys())

    config_path = config.get_config_path()
    remote_path = config_path.parent / "themes.json"
    if remote_path.exists():
        try:
            with remote_path.open() as f:
                remote = json.load(f)
            themes.extend(remote.keys())

        except (json.JSONDecodeError, OSError):
            pass

    return [t for t in themes if t.startswith(incomplete)]


def styles_autocomplete(incomplete: str) -> list[str]:
    """Return matching chart style completions."""
    return [s for s in styles.STYLES if s.startswith(incomplete)]


def setup_cli_environment(
    config_path: Path | None,
    output_dir: Path | None,
    verbose: bool,
    theme: str | None,
    stdout: bool,
    quiet: bool,
    require_token: bool,
) -> tuple[Config, bool, bool]:
    """Load config, configure logging, and create output directory.

    Parameters
    ----------
    config_path : Path | None
        Explicit config file path, or *None* for platform default.
    output_dir : Path | None
        Override for the output directory.
    verbose : bool
        Enable debug logging.
    theme : str | None
        Override for the chart theme.
    stdout : bool
        Send JSON to stdout (implies quiet and json_only).
    quiet : bool
        Suppress non-error log output.
    require_token : bool
        Whether a valid GitHub token must be present.

    Returns
    -------
    tuple[Config, bool, bool]
        ``(config, quiet, json_only)`` ready for the command handler.
    """
    if stdout:
        quiet = True
        json_only = True
    else:
        json_only = False

    log.logger.configure(verbose, quiet=quiet)

    cli_overrides = {
        "output_dir": output_dir,
        "verbose": verbose or None,
        "theme": theme,
    }

    cfg = config.load_config(
        config_path=config_path,
        cli_overrides=cli_overrides,
        require_token=require_token,
    )

    log.logger.configure(cfg.verbose, quiet=quiet)

    if not stdout:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        log.logger.info(f"Saving to {cfg.output_dir}")

    return cfg, quiet, json_only


@contextmanager
def handle_cli_errors() -> Iterator[None]:
    """Catch unexpected exceptions, log them, and exit with code 1.

    Raises
    ------
    typer.Exit
        Re-raised directly when the wrapped code calls ``typer.Exit``.
        All other exceptions are logged and converted to ``typer.Exit(1)``.
    """
    try:
        yield
    except typer.Exit:
        raise
    except Exception as e:
        log.logger.exception(f"Something went wrong: {e}")
        raise typer.Exit(1)
