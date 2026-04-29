from collections.abc import Callable
from typing import Final


STYLES: Final[tuple[str, ...]] = ("pixel", "pie", "bar")


def get_style_registry() -> dict[str, Callable[..., None]]:
    """Return the built-in style name to generator function mapping.

    Imports are deferred so matplotlib is not loaded until a chart is
    actually requested.

    Returns
    -------
    dict[str, Callable[..., None]]
        Style name to chart generator callable.
    """
    from .bar import generate_bar
    from .pie import generate_pie
    from .pixel import generate_pixel

    return {
        "pixel": generate_pixel,
        "pie": generate_pie,
        "bar": generate_bar,
    }
