"""Cozette bitmap font loader and text renderer"""

from functools import lru_cache
from pathlib import Path

from bdfparser import Font  # type: ignore[import-untyped]
from PIL import Image


@lru_cache(maxsize=1)
def load_cozette() -> Font:
    """Load Cozette BDF font, cached on first call"""
    font_path = Path(__file__).parent / "cozette.bdf"
    return Font(str(font_path))


def render_text(text: str, color: tuple[int, int, int], scale: int = 1) -> Image.Image:
    """Render text string as a PIL RGBA image using Cozette font"""
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
    assert pixels is not None

    for py in range(h):
        for px in range(w):
            *_, a = pixels[px, py]  # type: ignore[misc]
            if a > 0:
                pixels[px, py] = (*color, a)

    return img


def text_width(text: str, scale: int = 1) -> int:
    """Return the pixel width of rendered text at given scale"""
    return int(load_cozette().draw(text).width()) * scale


def text_height(scale: int = 1) -> int:
    """Return the pixel height for any text at given scale"""
    return int(load_cozette().headers["fbby"]) * scale
