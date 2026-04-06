"""Cozette bitmap font loader and text renderer."""

from functools import lru_cache
from pathlib import Path

from bdfparser import Font  # type: ignore[import-untyped]
from PIL import Image


@lru_cache(maxsize=1)
def load_cozette() -> Font:
    """Load the Cozette BDF bitmap font, cached after first call.

    Returns
    -------
    Font
        Parsed BDF font object.
    """
    font_path = Path(__file__).parent / "cozette.bdf"
    return Font(str(font_path))


def render_text(text: str, color: tuple[int, int, int], scale: int = 1) -> Image.Image:
    """Render a text string as a PIL RGBA image using the Cozette font.

    Parameters
    ----------
    text : str
        Text to render.
    color : tuple[int, int, int]
        Foreground RGB color.
    scale : int
        Integer scaling factor applied to the bitmap.

    Returns
    -------
    Image.Image
        RGBA image with transparent background and colored glyphs.
    """
    font = load_cozette()
    bm = font.draw(text)
    if scale > 1:
        bm = bm * scale

    w, h = bm.width(), bm.height()

    # tobytes('RGBA') gives white fg + transparent bg
    rgba_data = bm.tobytes("RGBA")
    img = Image.frombytes("RGBA", (w, h), rgba_data)

    # replace white foreground pixels with the requested color
    pixels = img.load()
    if pixels is None:
        raise ValueError("failed to load pixel data")

    for py in range(h):
        for px in range(w):
            *_, a = pixels[px, py]  # type: ignore[misc]
            if a > 0:
                pixels[px, py] = (*color, a)

    return img


def text_width(text: str, scale: int = 1) -> int:
    """Return the pixel width of *text* at the given scale.

    Parameters
    ----------
    text : str
        Text to measure.
    scale : int
        Integer scaling factor.

    Returns
    -------
    int
        Width in pixels.
    """
    return int(load_cozette().draw(text).width()) * scale


def text_height(scale: int = 1) -> int:
    """Return the line height in pixels at the given scale.

    Parameters
    ----------
    scale : int
        Integer scaling factor.

    Returns
    -------
    int
        Height in pixels.
    """
    return int(load_cozette().headers["fbby"]) * scale
