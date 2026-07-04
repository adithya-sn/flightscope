from __future__ import annotations

import math
import time

from .aircraft import Aircraft
from .config import AppConfig
from .geometry import bearing as calc_bearing
from .geometry import haversine

# Synthetic flights: (icao, callsign, bearing_from_obs_deg, distance_km, altitude_ft, speed_kt, track_deg, vrate_fpm)
_FLEET: list[tuple[str, str, float, float, int, float, float, int]] = [
    ("4b1a01", "AIQ101",  30.0,  8.0, 32000, 480, 210, 0),
    ("4b1a02", "IGO202",  80.0, 15.0, 28000, 420, 270,  -512),
    ("4b1a03", "SEJ303", 150.0, 22.0, 35000, 510, 350,  0),
    ("4b1a04", "AIC404", 220.0,  5.0,  5000, 180,  60, 1024),
    ("4b1a05", "VTI505", 300.0, 18.0, 41000, 540, 130,  0),
    ("4b1a06", "IND606", 340.0, 27.0,  8000, 240, 200, -256),
]

# Speed at which each aircraft moves (km/s along its track) for animation
_ANIM_SPEED_KM_S = 0.14   # ≈ 500 km/h in sim-time


def _offset_position(
    obs_lat: float,
    obs_lon: float,
    bearing_deg: float,
    distance_km: float,
) -> tuple[float, float]:
    """Return lat/lon of a point at (bearing, distance) from observer."""
    R = 6371.0
    ang = math.radians(bearing_deg)
    d_over_R = distance_km / R
    lat1 = math.radians(obs_lat)
    lon1 = math.radians(obs_lon)
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d_over_R)
        + math.cos(lat1) * math.sin(d_over_R) * math.cos(ang)
    )
    lon2 = lon1 + math.atan2(
        math.sin(ang) * math.sin(d_over_R) * math.cos(lat1),
        math.cos(d_over_R) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


class MockDatasource:
    """
    Returns synthetic aircraft that animate along their tracks.
    Drop-in replacement for Dump1090Client — same fetch() signature.
    Activated via `python -m flightscope.app --mock`.
    """

    def __init__(self, config: AppConfig) -> None:
        self._obs_lat = config.observer.lat
        self._obs_lon = config.observer.lon
        self._range_km = config.observer.range_km
        self._start = time.monotonic()
        # Initial (bearing, distance) for each aircraft, mutated each fetch
        self._state: list[list] = [
            [icao, cs, bear, dist, alt, spd, trk, vr]
            for icao, cs, bear, dist, alt, spd, trk, vr in _FLEET
        ]

    def fetch(self) -> list[Aircraft]:
        elapsed = time.monotonic() - self._start
        aircraft: list[Aircraft] = []

        for s in self._state:
            icao, callsign, bear_deg, dist_km, alt, spd, trk, vr = s

            # Animate: move each aircraft along its track
            lat, lon = _offset_position(self._obs_lat, self._obs_lon, bear_deg, dist_km)
            trk_rad = math.radians(trk)
            move_km = _ANIM_SPEED_KM_S * elapsed % self._range_km
            new_lat = lat + math.degrees(math.sin(trk_rad) * move_km / 6371.0)
            new_lon = lon + math.degrees(
                math.cos(trk_rad) * move_km / (6371.0 * math.cos(math.radians(lat)))
            )

            a = Aircraft(
                icao=icao,
                callsign=callsign,
                lat=new_lat,
                lon=new_lon,
                altitude=alt,
                speed=float(spd),
                track=float(trk),
                vertical_rate=vr,
            )
            a.distance_km = haversine(self._obs_lat, self._obs_lon, new_lat, new_lon)
            a.bearing_deg = calc_bearing(self._obs_lat, self._obs_lon, new_lat, new_lon)
            aircraft.append(a)

        aircraft.sort(key=lambda a: a.distance_km)
        return aircraft
