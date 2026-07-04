from __future__ import annotations

import math

from PIL import ImageDraw, ImageFont

from .aircraft import Aircraft
from .config import AppConfig
from .geometry import project_to_pixel

RADAR_CX: int = 64
RADAR_CY: int = 32
RADAR_RADIUS_PX: int = 30
RING_KM: tuple[int, ...] = (10, 20, 30)

_font = ImageFont.load_default()


def draw_radar(
    canvas: ImageDraw.ImageDraw,
    aircraft: list[Aircraft],
    selected: Aircraft | None,
    config: AppConfig,
) -> None:
    """
    Draw radar display onto canvas (128×64, 1-bit).
    Pure function — no I/O, no state. Modifies canvas in place.
    """
    cx, cy = RADAR_CX, RADAR_CY
    range_km = config.observer.range_km

    # 1. Range rings — scale to configured range
    for ring_km in RING_KM:
        ring_px = int((ring_km / range_km) * RADAR_RADIUS_PX)
        canvas.ellipse(
            (cx - ring_px, cy - ring_px, cx + ring_px, cy + ring_px),
            outline=1,
        )

    # 2. Compass cross
    canvas.line((cx - RADAR_RADIUS_PX, cy, cx + RADAR_RADIUS_PX, cy), fill=1)
    canvas.line((cx, cy - RADAR_RADIUS_PX, cx, cy + RADAR_RADIUS_PX), fill=1)

    # 3. North label
    canvas.text((cx - 3, cy - RADAR_RADIUS_PX - 8), "N", font=_font, fill=1)

    # 4. Non-selected aircraft as single pixels
    for ac in aircraft:
        if selected is not None and ac.icao == selected.icao:
            continue
        x, y = project_to_pixel(
            ac.bearing_deg, ac.distance_km, range_km, cx, cy, RADAR_RADIUS_PX
        )
        canvas.point((x, y), fill=1)

    # 5. Selected aircraft as circle + heading vector (drawn last, on top)
    if selected is not None:
        x, y = project_to_pixel(
            selected.bearing_deg, selected.distance_km, range_km, cx, cy, RADAR_RADIUS_PX
        )
        canvas.ellipse((x - 2, y - 2, x + 2, y + 2), outline=1)
        if selected.track is not None:
            theta = math.radians(selected.track)
            hx = x + 6 * math.sin(theta)
            hy = y - 6 * math.cos(theta)
            canvas.line((x, y, int(hx), int(hy)), fill=1)
