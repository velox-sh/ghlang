from pathlib import Path

from PIL import Image
from PIL import ImageDraw

from ..logging import logger
from ..static.fonts import render_text
from ..static.fonts import text_height
from ..static.fonts import text_width
from .constants import PIXEL_FONTSIZE
from .constants import PIXEL_LABEL_DOT
from .constants import PIXEL_LABEL_GAP
from .constants import PIXEL_LABEL_OFF
from .constants import PIXEL_PAD
from .constants import PIXEL_PX
from .constants import PIXEL_TITLE_FONTSIZE
from .constants import PIXEL_TITLE_GAP
from .constants import PIXEL_TOWER_CX
from .constants import PIXEL_TOWER_H
from .constants import PIXEL_TOWER_W
from .constants import ROUNDED_CORNER_RADIUS
from .constants import TOP_N
from .utils import add_rounded_corners
from .utils import build_display_segments
from .utils import get_theme
from .utils import hex_to_rgb


def _shade(rgb: tuple[int, int, int], f: float) -> tuple[int, int, int]:
    r, g, b = rgb
    return min(255, max(0, int(r * f))), min(255, max(0, int(g * f))), min(255, max(0, int(b * f)))


def _build_segments(
    language_stats: dict[str, int],
    colors: dict[str, str],
    top_n: int,
    fallback: tuple[int, int, int],
) -> list[tuple[str, float, tuple[int, int, int], int, int]]:
    """Build colored + positioned tower segments"""
    display = build_display_segments(language_stats, top_n)

    colored = [
        (name, pct, hex_to_rgb(colors[name]) if colors.get(name, "").startswith("#") else fallback)
        for name, pct in display
    ]

    total_pct = sum(pct for _, pct, _ in colored)

    # reversed so the smallest segment sits at the top of the tower
    ordered = list(reversed(colored))
    segs: list[tuple[str, float, tuple[int, int, int], int, int]] = []
    cursor = 0
    for i, (name, pct, color) in enumerate(ordered):
        h = (
            PIXEL_TOWER_H - cursor
            if i == len(ordered) - 1
            else max(3, round(PIXEL_TOWER_H * pct / total_pct))
        )
        segs.append((name, pct, color, cursor, cursor + h))
        cursor += h

    return segs


def _draw_iso_block(
    draw: ImageDraw.ImageDraw,
    cx: int,
    base_y: int,
    w_real: int,
    h_real: int,
    color: tuple[int, int, int],
) -> None:
    """Draw one isometric block using coords in real pixels"""
    hw = w_real // 2
    qw = w_real // 4
    top_y = base_y - h_real - qw * 2
    back = (cx, top_y)
    left = (cx - hw, top_y + qw)
    right = (cx + hw, top_y + qw)
    front_top = (cx, top_y + qw * 2)
    bot_left = (cx - hw, top_y + qw + h_real)
    bot_right = (cx + hw, top_y + qw + h_real)
    bot_front = (cx, top_y + qw * 2 + h_real)
    ec = _shade(color, 0.22)
    draw.polygon([left, front_top, bot_front, bot_left], fill=_shade(color, 0.70), outline=ec)
    draw.polygon([front_top, right, bot_right, bot_front], fill=_shade(color, 0.42), outline=ec)
    draw.polygon([back, right, front_top, left], fill=_shade(color, 1.28), outline=ec)


def generate_pixel(
    language_stats: dict[str, int],
    colors: dict[str, str],
    output: Path,
    title: str | None = None,
    theme: str = "light",
    top_n: int = TOP_N,
) -> None:
    """Generate a pixel-art isometric tower chart showing language distribution"""
    title = title if title else "Lang Stats"
    logger.debug(f"Generating pixel chart with {len(language_stats)} languages...")

    theme_colors = get_theme(theme)
    bg_rgb = hex_to_rgb(theme_colors["background"])
    title_rgb = hex_to_rgb(theme_colors["text"])
    fallback_rgb = hex_to_rgb(theme_colors["fallback"])

    segs = _build_segments(language_stats, colors, top_n, fallback_rgb)

    px = PIXEL_PX
    fs = PIXEL_FONTSIZE
    tfs = PIXEL_TITLE_FONTSIZE
    tw = PIXEL_TOWER_W
    th = PIXEL_TOWER_H
    cx_log = PIXEL_TOWER_CX
    hw = tw // 2
    qw = tw // 4

    label_strs = [f"{n}  {p:.1f}%" for n, p, *_ in segs]
    max_label_w_real = max((text_width(s, scale=fs) for s in label_strs), default=0)
    title_w_real = text_width(title, scale=tfs)
    font_h_real = text_height(scale=fs)
    title_h_real = text_height(scale=tfs)

    dot_area_real = (PIXEL_LABEL_GAP + PIXEL_LABEL_DOT + PIXEL_LABEL_OFF) * px
    label_start_real = (cx_log + hw) * px + dot_area_real

    title_area_real = title_h_real + PIXEL_TITLE_GAP * px
    top_extra_real = qw * 2 * px  # iso top cap extends above the tower rect

    content_h_real = title_area_real + top_extra_real + th * px + 4 * px
    content_w_real = max(
        label_start_real + max_label_w_real + 2 * px,
        (cx_log - hw) * px + title_w_real + 4 * px,
    )

    img_w = content_w_real + PIXEL_PAD * 2
    img_h = content_h_real + PIXEL_PAD * 2
    img_w = ((img_w + px - 1) // px) * px  # snap to px grid so no sub-pixel seams
    img_h = ((img_h + px - 1) // px) * px

    img = Image.new("RGBA", (img_w, img_h), (*bg_rgb, 255))
    draw = ImageDraw.Draw(img)

    cx_real = PIXEL_PAD + cx_log * px
    tower_base_real = PIXEL_PAD + title_area_real + top_extra_real + th * px

    for _, _, color, y_top, y_bot in segs:
        blk_base_real = tower_base_real - y_top * px
        blk_h_real = (y_bot - y_top) * px
        _draw_iso_block(draw, cx_real, blk_base_real, tw * px, blk_h_real, color)

    label_x0_real = cx_real + hw * px + PIXEL_LABEL_GAP * px

    for name, pct, color, y_top, y_bot in segs:
        screen_bot_real = tower_base_real - y_top * px
        screen_top_real = tower_base_real - y_bot * px - qw * 2 * px
        mid_y_real = (
            (screen_top_real + screen_bot_real) // 2 // px
        ) * px  # snap so connector aligns to pixel grid

        draw.rectangle(
            [cx_real + hw * px, mid_y_real - px, label_x0_real - 1, mid_y_real + px],
            fill=(*_shade(color, 0.42), 255),
        )

        dot_w_real = PIXEL_LABEL_DOT * px
        draw.rectangle(
            [label_x0_real, mid_y_real - px, label_x0_real + dot_w_real - 1, mid_y_real + px],
            fill=(*color, 255),
        )

        label_str = f"{name} {pct:.1f}%"
        text_x = label_x0_real + PIXEL_LABEL_DOT * px + PIXEL_LABEL_OFF * px
        text_y = mid_y_real - font_h_real // 2
        label_img = render_text(label_str, color, scale=fs)
        img.alpha_composite(label_img, dest=(text_x, text_y))

    title_img = render_text(title.upper(), title_rgb, scale=tfs)
    tx = (img_w - title_img.width) // 2
    ty = PIXEL_PAD
    img.alpha_composite(title_img, dest=(tx, ty))

    img = add_rounded_corners(img, radius=ROUNDED_CORNER_RADIUS)

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    logger.success(f"Saved pixel chart to {output}")
