from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing in degrees (0–360, clockwise from north) from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    y = math.sin(delta_lon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def project_to_pixel(
    bearing_deg: float,
    distance_km: float,
    range_km: float,
    cx: int,
    cy: int,
    radius_px: int,
) -> tuple[int, int]:
    """
    Map a (bearing, distance) pair to pixel coordinates on the radar disc.

    North-up: bearing 0° maps to top of display.
    Aircraft beyond range_km are clamped to the perimeter ring.
    """
    r_px = (distance_km / range_km) * radius_px
    theta = math.radians(bearing_deg)
    x = cx + r_px * math.sin(theta)
    y = cy - r_px * math.cos(theta)
    # Clamp to radar disc boundary
    x = max(cx - radius_px, min(cx + radius_px, x))
    y = max(cy - radius_px, min(cy + radius_px, y))
    return int(x), int(y)
