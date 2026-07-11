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
    dot_r = 3                           # non-selected dot radius (fixed small)
    tri_r = max(5, radius_px // 10)    # selected triangle half-size

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

    # 4. Non-selected aircraft — colour by altitude, skip if out of range
    for ac in aircraft:
        if selected is not None and ac.icao == selected.icao:
            continue
        if ac.distance_km >= range_km:
            continue
        x, y = project_to_pixel(ac.bearing_deg, ac.distance_km, range_km, cx, cy, radius_px)
        # Skip if dot would bleed outside the radar circle
        if math.hypot(x - cx, y - cy) > radius_px - dot_r:
            continue
        dot_color = _altitude_color(ac.altitude, fg)
        canvas.ellipse((x - dot_r, y - dot_r, x + dot_r, y + dot_r), fill=dot_color)

    # 5. Selected aircraft (drawn last, on top), skip if out of range
    if selected is not None and selected.distance_km <= range_km:
        x, y = project_to_pixel(
            selected.bearing_deg, selected.distance_km, range_km, cx, cy, radius_px
        )
        if selected.track is not None:
            canvas.polygon(_triangle(x, y, tri_r, selected.track), fill=accent)
        else:
            # Diamond when track unknown
            canvas.polygon(
                [(x, y - tri_r), (x + tri_r, y), (x, y + tri_r), (x - tri_r, y)],
                fill=accent,
            )


def _altitude_color(
    altitude: int | None,
    fg: int | tuple[int, int, int],
) -> int | tuple[int, int, int]:
    """Map altitude (ft) to a dot colour. Falls back to fg for 1-bit displays."""
    if not isinstance(fg, tuple):
        return fg
    if altitude is None:
        return (120, 120, 120)   # unknown — grey
    if altitude < 1_000:
        return (180, 40, 40)     # ground / low — red
    if altitude < 10_000:
        return (220, 200, 0)     # low-mid — yellow
    if altitude < 25_000:
        return (0, 220, 60)      # mid — green (same as fg)
    return (0, 200, 220)         # high — cyan


def _triangle(
    cx: int, cy: int, r: int, track_deg: float
) -> list[tuple[int, int]]:
    """
    Return three vertices of a filled triangle centred at (cx, cy),
    pointing in track_deg direction (0 = north-up), with tip-to-centre = r.
    """
    # tip points in direction of travel; base is opposite
    tip   = math.radians(track_deg)
    left  = math.radians(track_deg + 140)
    right = math.radians(track_deg - 140)
    def pt(angle: float, length: float) -> tuple[int, int]:
        return (int(cx + length * math.sin(angle)), int(cy - length * math.cos(angle)))
    return [pt(tip, r), pt(left, r * 0.65), pt(right, r * 0.65)]


def _dim_color(color: int | tuple[int, int, int]) -> int | tuple[int, int, int]:
    """Return a dimmer version of the foreground for grid lines."""
    if isinstance(color, int):
        return color  # 1-bit: no dimming possible
    r, g, b = color
    return (r // 3, g // 3, b // 3)
