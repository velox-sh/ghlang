from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from rich.console import Console
    from rich.progress import Progress


class Logger:
    """Loguru-style logger using Rich for output.

    Attributes
    ----------
    console : Console
        Rich console used for all output.
    """

    def __init__(self) -> None:
        self._console: Console | None = None
        self._verbose = False
        self._quiet = False

    @property
    def console(self) -> Console:
        if self._console is None:
            from rich.console import Console

            self._console = Console()
        return self._console

    def configure(self, verbose: bool = False, quiet: bool = False) -> None:
        """Configure verbosity level."""
        self._verbose = verbose
        self._quiet = quiet

    def info(self, msg: str) -> None:
        """Log an info message."""
        if not self._quiet:
            self.console.print(f"[blue]INFO[/]     {msg}")

    def debug(self, msg: str) -> None:
        """Log a debug message (only shown in verbose mode)."""
        if self._verbose and not self._quiet:
            self.console.print(f"[dim]DEBUG    {msg}[/]")

    def success(self, msg: str) -> None:
        """Log a success message."""
        if not self._quiet:
            self.console.print(f"[green]SUCCESS[/]  {msg}")

    def warning(self, msg: str) -> None:
        """Log a warning message."""
        self.console.print(f"[yellow]WARNING[/]  {msg}")

    def error(self, msg: str) -> None:
        """Log an error message."""
        self.console.print(f"[red]ERROR[/]    {msg}")

    def exception(self, msg: str) -> None:
        """Log an exception with traceback."""
        self.console.print(f"[red]ERROR[/]    {msg}")
        if self._verbose:
            self.console.print_exception()

    def progress(self) -> Progress:
        """Create a progress bar for long-running operations."""
        from rich.progress import BarColumn
        from rich.progress import Progress
        from rich.progress import SpinnerColumn
        from rich.progress import TaskProgressColumn
        from rich.progress import TextColumn

        return Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("({task.completed}/{task.total})"),
            console=self.console,
            disable=self._quiet,
        )

    def spinner(self) -> Progress:
        """Create a spinner for indeterminate operations."""
        from rich.progress import Progress
        from rich.progress import SpinnerColumn
        from rich.progress import TextColumn

        return Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            console=self.console,
            disable=self._quiet,
        )


logger = Logger()
