from __future__ import annotations

import math

from PIL import ImageDraw, ImageFont

from .aircraft import Aircraft
from .config import AppConfig
from .display import DisplayBackend
from .geometry import project_to_pixel

RING_KM: tuple[int, ...] = (10, 20, 30)

_font_small = ImageFont.load_default()


def _radar_geometry(backend: DisplayBackend) -> tuple[int, int, int]:
    """Return (cx, cy, radius_px) for the radar disc, scaled to panel size."""
    w, h = backend.PANEL_WIDTH, backend.PANEL_HEIGHT
    cx = w // 2
    cy = h // 2
    radius_px = min(w, h) // 2 - 6   # 6px margin from edge
    return cx, cy, radius_px


def draw_radar(
    canvas: ImageDraw.ImageDraw,
    aircraft: list[Aircraft],
    selected: Aircraft | None,
    config: AppConfig,
    backend: DisplayBackend,
) -> None:
    """
    Draw radar onto canvas. Pure function — no I/O, no state.

    Colors and dimensions are taken from backend so the same function
    works for 1-bit OLEDs and colour TFT/pygame backends.
    """
    cx, cy, radius_px = _radar_geometry(backend)
    range_km = config.observer.range_km
    fg = backend.COLOR_FG
    accent = backend.COLOR_ACCENT
    dim = _dim_color(fg)  # dimmer shade for rings/cross

    # Ring line width scales with panel size
    ring_w = max(1, radius_px // 30)
    vec_len = max(8, radius_px // 4)   # heading vector length
    dot_r = max(1, radius_px // 20)    # non-selected dot radius
    sel_r = max(3, radius_px // 10)    # selected circle radius

    # 1. Range rings
    for ring_km in RING_KM:
        ring_px = int((ring_km / range_km) * radius_px)
        canvas.ellipse(
            (cx - ring_px, cy - ring_px, cx + ring_px, cy + ring_px),
            outline=dim,
            width=ring_w,
        )

    # 2. Compass cross (dimmed)
    canvas.line((cx - radius_px, cy, cx + radius_px, cy), fill=dim, width=ring_w)
    canvas.line((cx, cy - radius_px, cx, cy + radius_px), fill=dim, width=ring_w)

    # 3. North label
    canvas.text((cx - 4, cy - radius_px - 14), "N", font=_font_small, fill=fg)

    # 4. Non-selected aircraft
    for ac in aircraft:
        if selected is not None and ac.icao == selected.icao:
            continue
        x, y = project_to_pixel(ac.bearing_deg, ac.distance_km, range_km, cx, cy, radius_px)
        canvas.ellipse((x - dot_r, y - dot_r, x + dot_r, y + dot_r), fill=fg)

    # 5. Selected aircraft (drawn last, on top)
    if selected is not None:
        x, y = project_to_pixel(
            selected.bearing_deg, selected.distance_km, range_km, cx, cy, radius_px
        )
        canvas.ellipse((x - sel_r, y - sel_r, x + sel_r, y + sel_r), outline=accent, width=ring_w)
        if selected.track is not None:
            theta = math.radians(selected.track)
            hx = x + vec_len * math.sin(theta)
            hy = y - vec_len * math.cos(theta)
            canvas.line((x, y, int(hx), int(hy)), fill=accent, width=ring_w)


def _dim_color(color: int | tuple[int, int, int]) -> int | tuple[int, int, int]:
    """Return a dimmer version of the foreground for grid lines."""
    if isinstance(color, int):
        return color  # 1-bit: no dimming possible
    r, g, b = color
    return (r // 3, g // 3, b // 3)
