"""Chart rendering styles"""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol


class StyleFn(Protocol):
    """Protocol all chart style callables must conform to"""

    def __call__(
        self,
        language_stats: dict[str, int],
        colors: dict[str, str],
        output: Path,
        title: str | None,
        theme: str,
        **kwargs: object,
    ) -> None: ...


STYLES: tuple[str, ...] = ("pixel", "pie", "bar")


def get_style_registry() -> dict[str, Callable[..., None]]:
    """Return the built-in style registry (lazy to avoid eager matplotlib import)"""
    from .bar import generate_bar  # noqa: PLC0415
    from .pie import generate_pie  # noqa: PLC0415
    from .pixel import generate_pixel  # noqa: PLC0415

    return {
        "pixel": generate_pixel,
        "pie": generate_pie,
        "bar": generate_bar,
    }
