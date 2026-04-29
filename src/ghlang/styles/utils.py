import io
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image
from PIL import ImageDraw

from . import constants


def build_display_segments(
    language_stats: dict[str, int],
    top_n: int,
) -> list[tuple[str, float]]:
    """Build display segments from raw language stats.

    Keep the top *top_n* languages above the hide threshold and fold the
    remainder into an "Other" bucket.

    Parameters
    ----------
    language_stats : dict[str, int]
        Language name to count mapping.
    top_n : int
        Maximum number of individual language segments.

    Returns
    -------
    list[tuple[str, float]]
        ``(name, percentage)`` pairs, possibly ending with ``("Other", ...)``.
    """
    items = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    total = sum(language_stats.values()) or 1

    shown: list[tuple[str, float]] = []
    others_pct = 0.0

    for i, (name, count) in enumerate(items):
        pct = count / total * 100
        if i < top_n and pct >= constants.HIDE_THRESHOLD:
            shown.append((name, pct))
        else:
            others_pct += pct

    if others_pct > 0:
        shown.append(("Other", round(others_pct, 1)))

    return shown


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a ``#RRGGBB`` hex string to an ``(R, G, B)`` tuple.

    Parameters
    ----------
    hex_color : str
        Hex color string, with or without leading ``#``.

    Returns
    -------
    tuple[int, int, int]
        Red, green, blue channel values (0-255).
    """
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def add_rounded_corners(
    img: Image.Image, radius: int = constants.ROUNDED_CORNER_RADIUS
) -> Image.Image:
    """Return a copy of *img* with rounded-corner alpha masking applied.

    Parameters
    ----------
    img : Image.Image
        Source image (converted to RGBA internally).
    radius : int
        Corner radius in pixels.

    Returns
    -------
    Image.Image
        RGBA image with transparent corners.
    """
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def save_matplotlib_chart(output: Path, background_color: str) -> None:
    """Save the current matplotlib figure to PNG with rounded corners.

    Parameters
    ----------
    output : Path
        Destination file path. Parent directories are created if needed.
    background_color : str
        Hex color used as the figure face color.
    """
    # TODO: re-enable SVG support once PNG pipeline is stable
    output.parent.mkdir(parents=True, exist_ok=True)

    buf = io.BytesIO()
    plt.savefig(
        buf, format="png", dpi=constants.PNG_DPI, bbox_inches="tight", facecolor=background_color
    )
    plt.close()
    buf.seek(0)

    img = Image.open(buf)

    rounded = add_rounded_corners(img)
    rounded.save(output)
