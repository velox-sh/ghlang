import os
from pathlib import Path
import platform
import subprocess

import typer

from ghlang import config as ghlang_config
from ghlang import exceptions
from ghlang.display import config as display_config


def _open_in_editor(path: Path) -> None:
    """Open a file in the user's editor or system default"""
    editor = os.environ.get("EDITOR")

    if editor:
        subprocess.run([editor, str(path)], check=False)
    elif platform.system() == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    elif platform.system() == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Print config as formatted table",
    ),
    path: bool = typer.Option(
        False,
        "--path",
        help="Print config file path",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Print raw config file contents",
    ),
) -> None:
    """Manage config file"""
    config_path = ghlang_config.get_config_path()

    if path:
        print(config_path)
        return

    if raw:
        if not config_path.exists():
            typer.echo(f"Config file doesn't exist yet: {config_path}")
            raise typer.Exit(1)

        display_config.print_raw_config(config_path)
        return

    if show:
        if not config_path.exists():
            typer.echo(f"Config file doesn't exist yet: {config_path}")
            raise typer.Exit(1)

        try:
            cfg = ghlang_config.load_config(config_path=config_path, require_token=False)
        except (exceptions.ConfigError, ValueError) as e:
            typer.echo(f"Error loading config: {e}")
            raise typer.Exit(1)

        display_config.print_config(cfg, config_path)
        return

    if not config_path.exists():
        ghlang_config.create_default_config(config_path)
        typer.echo(f"Created config at {config_path}")

    _open_in_editor(config_path)
