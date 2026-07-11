from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .aircraft import Aircraft
from .display import DisplayBackend
from .metar import Metar, CATEGORY_COLORS
from .tracker import SelectionMode

# Common monospace TTF paths: Pi OS (DejaVu), macOS (Menlo)
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]


def _load_ttf(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


# Font sizes tuned for 240×320 panel
_font_cs   = _load_ttf(36)  # callsign
_font_data = _load_ttf(14)  # ALT/SPD/DST/HDG
_font_meta = _load_ttf(12)  # METAR rows + mode label

_MODE_LABELS = {
    SelectionMode.AUTO:   "[AUTO]",
    SelectionMode.ROTATE: "[ROT]",
    SelectionMode.LOCK:   "[LOCK]",
}


def draw_info(
    img: Image.Image,
    aircraft: Aircraft | None,
    mode: SelectionMode,
    backend: DisplayBackend,
    metar: Metar | None = None,
) -> None:
    w, h = img.size
    canvas = ImageDraw.Draw(img)
    fg = backend.COLOR_FG
    mode_label = _MODE_LABELS[mode]

    if aircraft is None:
        canvas.text((4, h // 2 - 10), "NO AIRCRAFT", font=_font_data, fill=fg)
        _draw_mode(canvas, mode_label, w, h, fg)
        return

    # --- Callsign ---
    cs = aircraft.display_callsign()
    cs_bb = canvas.textbbox((2, 2), cs, font=_font_cs)
    canvas.text((2, 2), cs, font=_font_cs, fill=fg)

    # Separator below actual rendered bottom of callsign
    sep_y = cs_bb[3] + 4
    canvas.line((0, sep_y, w - 1, sep_y), fill=fg)

    # --- Two-column data rows ---
    data_y = sep_y + 6
    row_h = _font_data.size + 6

    alt_str = f"ALT {aircraft.altitude_str()} {aircraft.vrate_symbol()}"
    dst_str = f"DST {aircraft.distance_km:.1f}km"
    hdg = f"HDG {aircraft.track:.0f}°" if aircraft.track is not None else "HDG ---"

    # Right column starts past the widest left string
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    left_w = max(
        probe.textbbox((0, 0), alt_str, font=_font_data)[2],
        probe.textbbox((0, 0), dst_str, font=_font_data)[2],
    )
    col_r = left_w + 10

    canvas.text((2, data_y),          alt_str,                    font=_font_data, fill=fg)
    canvas.text((2, data_y + row_h),  dst_str,                    font=_font_data, fill=fg)
    canvas.text((col_r, data_y),      f"SPD {aircraft.speed_str()}", font=_font_data, fill=fg)
    canvas.text((col_r, data_y + row_h), hdg,                    font=_font_data, fill=fg)

    if metar is not None:
        _draw_metar(canvas, metar, w, h, fg, img.mode)

    _draw_mode(canvas, mode_label, w, h, fg)


def _draw_metar(
    canvas: ImageDraw.ImageDraw,
    metar: Metar,
    w: int,
    h: int,
    fg: int | tuple[int, int, int],
    img_mode: str = "RGB",
) -> None:
    metar_y = h // 2 + 6
    row = _font_meta.size + 4

    cat_color: tuple[int, int, int]
    if isinstance(fg, tuple):
        cat_color = CATEGORY_COLORS.get(metar.category, fg)
    else:
        cat_color = fg

    canvas.line((0, metar_y - 4, w - 1, metar_y - 4), fill=fg)

    # Station left, category badge right
    canvas.text((2, metar_y), metar.station, font=_font_meta, fill=fg)
    cat_bb = canvas.textbbox((0, 0), metar.category, font=_font_meta)
    cat_w = cat_bb[2] - cat_bb[0]
    canvas.text((w - cat_w - 2, metar_y), metar.category, font=_font_meta, fill=cat_color)

    canvas.text((2, metar_y + row), f"WND {metar.wind_str()}", font=_font_meta, fill=fg)

    # Right column past widest left string
    probe = ImageDraw.Draw(Image.new(img_mode, (1, 1)))
    left_strs = [f"VIS {metar.visibility}m", f"SKY {metar.sky}"]
    mcol_r = max(probe.textbbox((0, 0), s, font=_font_meta)[2] for s in left_strs) + 8

    canvas.text((2,       metar_y + row * 2), f"VIS {metar.visibility}m", font=_font_meta, fill=fg)
    canvas.text((mcol_r,  metar_y + row * 2), f"T {metar.temp_str()}",    font=_font_meta, fill=fg)
    canvas.text((2,       metar_y + row * 3), f"SKY {metar.sky}",          font=_font_meta, fill=fg)
    canvas.text((mcol_r,  metar_y + row * 3), metar.altimeter,             font=_font_meta, fill=fg)

    if metar.wx:
        canvas.text((2, metar_y + row * 4), metar.wx, font=_font_meta, fill=fg)


def _draw_mode(
    canvas: ImageDraw.ImageDraw,
    label: str,
    w: int,
    h: int,
    fg: int | tuple[int, int, int],
) -> None:
    bb = canvas.textbbox((0, 0), label, font=_font_meta)
    text_w = bb[2] - bb[0]
    text_h = bb[3] - bb[1]
    canvas.text((w - text_w - 2, h - text_h - 4), label, font=_font_meta, fill=fg)
