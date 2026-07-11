from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .aircraft import Aircraft
from .display import DisplayBackend
from .metar import Metar, CATEGORY_COLORS
from .tracker import SelectionMode

_font = ImageFont.load_default()

_MODE_LABELS = {
    SelectionMode.AUTO:   "[AUTO]",
    SelectionMode.ROTATE: "[ROT]",
    SelectionMode.LOCK:   "[LOCK]",
}


_DATA_SCALE = 2   # scale factor for data rows (ALT/SPD/DST/HDG)
_DATA_ROW_H = 10 * _DATA_SCALE + 4  # pixel height of one scaled data row


def draw_info(
    img: Image.Image,
    aircraft: Aircraft | None,
    mode: SelectionMode,
    backend: DisplayBackend,
    metar: Metar | None = None,
) -> None:
    """
    Draw info panel onto img. Pure function — no I/O, no state.

    Scales layout to img dimensions and uses backend colors.
    """
    w, h = img.size
    canvas = ImageDraw.Draw(img)
    fg = backend.COLOR_FG
    mode_label = _MODE_LABELS[mode]

    if aircraft is None:
        _paste_scaled_text(img, (4, h // 2 - 10), "NO AIRCRAFT", 2, fg)
        _draw_mode(canvas, mode_label, w, h, fg)
        return

    # Callsign scale: largest integer scale that fits width and ~25% height
    cs_target_h = h // 4
    scale_by_h = max(1, cs_target_h // 10)
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    cs_bbox = probe.textbbox((0, 0), aircraft.display_callsign(), font=_font)
    cs_text_w = cs_bbox[2] - cs_bbox[0]
    scale_by_w = max(1, (w - 4) // cs_text_w) if cs_text_w > 0 else scale_by_h
    cs_scale = min(scale_by_h, scale_by_w)

    # --- Callsign ---
    cs_h = 10 * cs_scale
    _paste_scaled_text(img, (2, 2), aircraft.display_callsign(), cs_scale, fg)

    # Separator
    sep_y = cs_h + 4
    canvas.line((0, sep_y, w - 1, sep_y), fill=fg)

    # --- Two-column data rows at 2× scale ---
    # Left column width: widest of the two left strings
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    alt_str = f"ALT {aircraft.altitude_str()} {aircraft.vrate_symbol()}"
    dst_str = f"DST {aircraft.distance_km:.1f}km"
    left_w = max(
        probe.textbbox((0, 0), alt_str, font=_font)[2],
        probe.textbbox((0, 0), dst_str, font=_font)[2],
    ) * _DATA_SCALE + 6
    col_r = max(w // 2, left_w)

    data_y = sep_y + 6
    hdg = f"HDG {aircraft.track:.0f}°" if aircraft.track is not None else "HDG ---"

    _paste_scaled_text(img, (2, data_y),                   alt_str, _DATA_SCALE, fg)
    _paste_scaled_text(img, (2, data_y + _DATA_ROW_H),    dst_str, _DATA_SCALE, fg)
    _paste_scaled_text(img, (col_r, data_y),               f"SPD {aircraft.speed_str()}", _DATA_SCALE, fg)
    _paste_scaled_text(img, (col_r, data_y + _DATA_ROW_H), hdg, _DATA_SCALE, fg)

    if metar is not None:
        _draw_metar(canvas, img, metar, w, h, fg)

    _draw_mode(canvas, mode_label, w, h, fg)


def _paste_scaled_text(
    img: Image.Image,
    pos: tuple[int, int],
    text: str,
    scale: int,
    color: int | tuple[int, int, int],
) -> None:
    """Render text at scale× and paste onto img, in the given color."""
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    bbox = probe.textbbox((0, 0), text, font=_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if w <= 0 or h <= 0:
        return

    small = Image.new(img.mode, (w, h))
    ImageDraw.Draw(small).text((0, -bbox[1]), text, font=_font, fill=color)
    big = small.resize((w * scale, h * scale), resample=Image.NEAREST)
    img.paste(big, pos)


_METAR_SCALE = 2
_METAR_ROW_H = 10 * _METAR_SCALE + 4


def _draw_metar(
    canvas: ImageDraw.ImageDraw,
    img: Image.Image,
    metar: Metar,
    w: int,
    h: int,
    fg: int | tuple[int, int, int],
) -> None:
    """
    Render METAR strip in the lower portion of the info panel.

    Layout (from y≈h//2+6 on a 320px panel):
      separator line
      station + category badge
      wind
      visibility  temp/dew
      sky         altimeter
      wx (if present)
    """
    metar_y = h // 2 + 6
    row = _METAR_ROW_H
    col_r = w // 2

    cat_color: tuple[int, int, int]
    if isinstance(fg, tuple):
        cat_color = CATEGORY_COLORS.get(metar.category, fg)
    else:
        cat_color = fg

    canvas.line((0, metar_y - 4, w - 1, metar_y - 4), fill=fg)

    # Station left, category badge right — both 2×
    _paste_scaled_text(img, (2, metar_y), metar.station, _METAR_SCALE, fg)
    cat_label = metar.category
    cat_w = canvas.textbbox((0, 0), cat_label, font=_font)[2] * _METAR_SCALE
    _paste_scaled_text(img, (w - cat_w - 2, metar_y), cat_label, _METAR_SCALE, cat_color)

    _paste_scaled_text(img, (2, metar_y + row), f"WND {metar.wind_str()}", _METAR_SCALE, fg)

    # Right column: past the widest left-side string
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    left_strs = [f"VIS {metar.visibility}m", f"SKY {metar.sky}"]
    mcol_r = max(probe.textbbox((0,0), s, font=_font)[2] for s in left_strs) * _METAR_SCALE + 8

    _paste_scaled_text(img, (2,       metar_y + row*2), f"VIS {metar.visibility}m", _METAR_SCALE, fg)
    _paste_scaled_text(img, (mcol_r,  metar_y + row*2), f"T {metar.temp_str()}",    _METAR_SCALE, fg)
    _paste_scaled_text(img, (2,       metar_y + row*3), f"SKY {metar.sky}",          _METAR_SCALE, fg)
    _paste_scaled_text(img, (mcol_r,  metar_y + row*3), metar.altimeter,             _METAR_SCALE, fg)

    if metar.wx:
        _paste_scaled_text(img, (2, metar_y + row*4), metar.wx, _METAR_SCALE, fg)


def _draw_mode(
    canvas: ImageDraw.ImageDraw,
    label: str,
    w: int,
    h: int,
    fg: int | tuple[int, int, int],
) -> None:
    """Right-align mode label at the bottom of the panel."""
    bbox = canvas.textbbox((0, 0), label, font=_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = w - text_w - 2
    y = h - text_h - 4
    canvas.text((max(0, x), y), label, font=_font, fill=fg)
