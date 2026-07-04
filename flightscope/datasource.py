from __future__ import annotations

import sys

import requests

from .aircraft import Aircraft
from .config import AppConfig
from .geometry import bearing as calc_bearing
from .geometry import haversine


class Dump1090Client:
    def __init__(self, config: AppConfig) -> None:
        self._url = config.source.url
        self._obs_lat = config.observer.lat
        self._obs_lon = config.observer.lon

    def fetch(self) -> list[Aircraft]:
        """
        Fetch and parse aircraft.json.
        Returns Aircraft list sorted by distance_km ascending.
        Never raises — returns [] on any error.
        """
        try:
            response = requests.get(self._url, timeout=2.0)
            response.raise_for_status()
            raw_list = response.json()["aircraft"]
        except Exception as exc:
            print(f"[datasource] fetch error: {exc}", file=sys.stderr)
            return []

        aircraft: list[Aircraft] = []
        for entry in raw_list:
            if "lat" not in entry or "lon" not in entry:
                continue
            try:
                a = self._parse(entry)
            except Exception as exc:
                print(f"[datasource] parse error for {entry.get('hex', '?')}: {exc}", file=sys.stderr)
                continue
            aircraft.append(a)

        aircraft.sort(key=lambda a: a.distance_km)
        return aircraft

    def _parse(self, entry: dict) -> Aircraft:
        lat = float(entry["lat"])
        lon = float(entry["lon"])

        raw_alt = entry.get("altitude")
        if raw_alt == "ground":
            altitude: int | None = 0
        elif raw_alt is not None:
            altitude = int(raw_alt)
        else:
            altitude = None

        raw_speed = entry.get("speed")
        speed: float | None = float(raw_speed) if raw_speed is not None else None

        raw_track = entry.get("track")
        track: float | None = float(raw_track) if raw_track is not None else None

        raw_vr = entry.get("vert_rate")
        vertical_rate: int | None = int(raw_vr) if raw_vr is not None else None

        a = Aircraft(
            icao=str(entry.get("hex", "")).strip(),
            callsign=str(entry.get("flight", "")).strip(),
            lat=lat,
            lon=lon,
            altitude=altitude,
            speed=speed,
            track=track,
            vertical_rate=vertical_rate,
        )
        a.distance_km = haversine(self._obs_lat, self._obs_lon, lat, lon)
        a.bearing_deg = calc_bearing(self._obs_lat, self._obs_lon, lat, lon)
        return a
