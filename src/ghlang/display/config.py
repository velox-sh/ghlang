from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table


if TYPE_CHECKING:
    from ghlang.config import Config


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return "[green]true[/green]" if value else "[red]false[/red]"

    if isinstance(value, list):
        if not value:
            return "[dim][][/dim]"

        return ", ".join(str(v) for v in value)

    if isinstance(value, Path):
        return str(value)

    return str(value)


def print_config(cfg: "Config", config_path: Path) -> None:
    """Print the active configuration as Rich-formatted section tables.

    Parameters
    ----------
    cfg : Config
        Loaded configuration dataclass.
    config_path : Path
        Path to the config file (shown as a header).
    """
    console = Console()
    console.print(f"\n[bold]Config:[/bold] {config_path}\n")

    sections = [
        (
            "GitHub",
            [
                ("token", cfg.token if cfg.token else "[dim]not set[/dim]"),
                ("affiliation", cfg.affiliation),
                ("visibility", cfg.visibility),
                ("ignored_repos", _format_value(cfg.ignored_repos)),
            ],
        ),
        (
            "Tokount",
            [("ignored_dirs", _format_value(cfg.ignored_dirs))],
        ),
        (
            "Output",
            [("directory", str(cfg.output_dir))],
        ),
        (
            "Preferences",
            [
                ("verbose", _format_value(cfg.verbose)),
                ("theme", cfg.theme),
            ],
        ),
    ]

    for section_name, rows in sections:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        console.print(f"[bold yellow]{section_name}[/bold yellow]")

        for key, val in rows:
            table.add_row(key, val)

        console.print(table)
        console.print()


def print_raw_config(config_path: Path) -> None:
    """Print the raw TOML config file with syntax highlighting.

    Parameters
    ----------
    config_path : Path
        Path to the TOML config file.
    """
    console = Console()
    syntax = Syntax(config_path.read_text(), "toml", theme="ansi_dark", line_numbers=True)
    console.print(syntax)
