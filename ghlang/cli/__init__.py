"""CLI entry point and command registration"""

import typer

from ghlang import __version__

from .config import config as config_cmd
from .github import github as github_cmd
from .local import local as local_cmd
from .theme import theme as theme_cmd


app = typer.Typer(help="See what languages you've been coding in", add_completion=True)
app.command()(config_cmd)
app.command()(github_cmd)
app.command()(local_cmd)
app.command()(theme_cmd)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"ghlang v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


if __name__ == "__main__":
    app()
