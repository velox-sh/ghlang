from rich.console import Console
from rich.table import Table


def print_theme_info(
    name: str,
    colors: dict[str, str],
    source: str,
    is_active: bool,
) -> None:
    """Print a single theme's color keys, hex values, and swatches.

    Parameters
    ----------
    name : str
        Theme name.
    colors : dict[str, str]
        Color key to hex value mapping.
    source : str
        Origin label (built-in, remote, custom).
    is_active : bool
        Whether this theme is currently active.
    """
    console = Console()
    active_tag = "  [green]*active[/green]" if is_active else ""
    console.print(f"\n[bold cyan]{name}[/bold cyan]  [dim]({source})[/dim]{active_tag}\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Hex")
    table.add_column("Swatch")

    for key, hex_val in colors.items():
        table.add_row(key, hex_val, f"[on {hex_val}]   [/on {hex_val}]")

    console.print(table)
    console.print()


def print_theme_list(
    built_in: dict[str, dict[str, str]],
    remote: dict[str, dict[str, str]],
    custom: dict[str, dict[str, str]],
    active: str,
) -> None:
    """Print all themes grouped by source with an active marker.

    Parameters
    ----------
    built_in : dict[str, dict[str, str]]
        Built-in theme registry.
    remote : dict[str, dict[str, str]]
        Remote theme registry.
    custom : dict[str, dict[str, str]]
        Custom theme registry.
    active : str
        Name of the currently active theme (marked with ``*``).
    """
    console = Console()

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Theme", style="cyan")
    table.add_column("Source")
    table.add_column("")

    for source_label, themes_dict in [
        ("built-in", built_in),
        ("remote", remote),
        ("custom", custom),
    ]:
        for theme_name in sorted(themes_dict):
            marker = "[green]*[/green]" if theme_name == active else ""
            table.add_row(theme_name, source_label, marker)

    console.print()
    console.print(table)
    console.print(f"\n  [dim]* = active theme ({active})[/dim]\n")
