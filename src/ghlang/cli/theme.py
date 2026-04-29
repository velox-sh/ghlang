from rich.console import Console
import typer

from ghlang import themes
from ghlang import utils
from ghlang.display import themes as display_themes
from ghlang.static import themes as static_themes

from . import utils as cli_utils


def theme(
    list_themes: bool = typer.Option(
        False,
        "--list",
        help="List all available themes",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Force-refresh remote themes (bypass 1-day cache)",
    ),
    info: str | None = typer.Option(
        None,
        "--info",
        help="Show details for a theme",
    ),
) -> None:
    """Manage themes"""
    with cli_utils.handle_cli_errors():
        console = Console()
        config_dir = utils.get_config_dir()

        if refresh:
            refreshed = themes.load_all_themes(config_dir, force_refresh=True)
            remote_count = len(refreshed) - len(static_themes.THEMES)
            console.print(
                f"[green]Refreshed[/green] remote themes: {remote_count} remote theme(s) loaded"
            )
            return

        active = utils.get_active_theme()
        built_in, remote, custom = utils.load_themes_by_source(config_dir)

        if info and not list_themes:
            all_themes: dict[str, dict[str, str]] = {**built_in, **remote, **custom}
            if info not in all_themes:
                console.print(f"[red]Theme '{info}' not found[/red]")
                raise typer.Exit(1)

            colors = all_themes[info]

            if info in custom:
                source = "custom"
            elif info in remote:
                source = "remote"
            else:
                source = "built-in"

            display_themes.print_theme_info(info, colors, source, is_active=info == active)
            return

        display_themes.print_theme_list(built_in, remote, custom, active)
