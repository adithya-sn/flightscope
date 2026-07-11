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

    # Callsign scale: largest integer scale that fits both width and ~25% height
    cs_target_h = h // 4
    scale_by_h = max(1, cs_target_h // 10)
    probe = ImageDraw.Draw(Image.new(img.mode, (1, 1)))
    cs_bbox = probe.textbbox((0, 0), aircraft.display_callsign() if aircraft else "W", font=_font)
    cs_text_w = cs_bbox[2] - cs_bbox[0]
    scale_by_w = max(1, (w - 4) // cs_text_w) if cs_text_w > 0 else scale_by_h
    cs_scale = min(scale_by_h, scale_by_w)

    # Data section starts below callsign + separator
    cs_h = 10 * cs_scale
    sep_y = cs_h + 2
    data_y = sep_y + 4
    row_h = max(10, (h - data_y - 14) // 4)  # 4 data rows + mode line

    if aircraft is None:
        cx = w // 2
        cy = h // 2
        canvas.text((cx - 30, cy - 5), "NO AIRCRAFT", font=_font, fill=fg)
        _draw_mode(canvas, mode_label, w, h, fg)
        return

    # --- Callsign ---
    _paste_scaled_text(img, (2, 2), aircraft.display_callsign(), cs_scale, fg)

    # Separator
    canvas.line((0, sep_y, w - 1, sep_y), fill=fg)

    # --- Two-column data rows ---
    col_r = w // 2

    canvas.text((2, data_y),           f"ALT {aircraft.altitude_str()} {aircraft.vrate_symbol()}", font=_font, fill=fg)
    canvas.text((2, data_y + row_h),   f"DST {aircraft.distance_km:.1f}km", font=_font, fill=fg)

    hdg = f"HDG {aircraft.track:.0f}°" if aircraft.track is not None else "HDG ---"
    canvas.text((col_r, data_y),         f"SPD {aircraft.speed_str()}", font=_font, fill=fg)
    canvas.text((col_r, data_y + row_h), hdg, font=_font, fill=fg)

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

    Layout (from y=160 on a 320px panel):
      separator line
      station + category badge
      wind
      visibility  temp/dew
      sky         altimeter
      wx (if present)
    """
    # Anchor: below aircraft data, above mode indicator
    metar_y = h // 2 + 10
    row = 12  # px per metar row

    # Category color overrides fg for the badge
    cat_color: tuple[int, int, int]
    if isinstance(fg, tuple):
        cat_color = CATEGORY_COLORS.get(metar.category, fg)
    else:
        cat_color = fg  # 1-bit: no color

    # Separator
    canvas.line((0, metar_y - 4, w - 1, metar_y - 4), fill=fg)

    # Station + category
    canvas.text((2, metar_y), f"{metar.station}", font=_font, fill=fg)
    cat_label = metar.category
    cat_bbox = canvas.textbbox((0, 0), cat_label, font=_font)
    cat_w = cat_bbox[2] - cat_bbox[0]
    canvas.text((w - cat_w - 2, metar_y), cat_label, font=_font, fill=cat_color)

    # Wind
    canvas.text((2, metar_y + row), f"WND {metar.wind_str()}", font=_font, fill=fg)

    # Visibility | Temp/dew
    canvas.text((2,       metar_y + row * 2), f"VIS {metar.visibility}m", font=_font, fill=fg)
    canvas.text((w // 2,  metar_y + row * 2), f"T {metar.temp_str()}", font=_font, fill=fg)

    # Sky | Altimeter
    canvas.text((2,       metar_y + row * 3), f"SKY {metar.sky}", font=_font, fill=fg)
    canvas.text((w // 2,  metar_y + row * 3), metar.altimeter, font=_font, fill=fg)

    # Significant weather (only if present)
    if metar.wx:
        canvas.text((2, metar_y + row * 4), metar.wx, font=_font, fill=fg)


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
