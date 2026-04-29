import importlib

import click
import typer
from typer.core import TyperGroup
from typer.main import CommandInfo
from typer.main import get_command_from_info

from ghlang import __doc__
from ghlang import __version__


_LAZY_COMMANDS = {
    "config": ("ghlang.cli.config", "config"),
    "github": ("ghlang.cli.github", "github"),
    "local": ("ghlang.cli.local", "local"),
    "theme": ("ghlang.cli.theme", "theme"),
}


class _LazyGroup(TyperGroup):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:  # noqa: ARG002
        """Return a command by name, lazily loading it if necessary."""
        if cmd_name in self.commands:
            return self.commands[cmd_name]

        if cmd_name in _LAZY_COMMANDS:
            mod_path, func_name = _LAZY_COMMANDS[cmd_name]

            mod = importlib.import_module(mod_path)
            func = getattr(mod, func_name)

            cmd = get_command_from_info(
                command_info=CommandInfo(name=cmd_name, callback=func),
                pretty_exceptions_short=True,
                rich_markup_mode=None,
            )

            self.commands[cmd_name] = cmd
            return cmd

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:  # noqa: ARG002
        """Return a list of command names, including lazy-loaded ones."""
        regular = list(self.commands.keys())
        lazy = [k for k in _LAZY_COMMANDS if k not in self.commands]
        return regular + lazy


app = typer.Typer(
    help=__doc__,
    add_completion=True,
    cls=_LazyGroup,
)


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
