from __future__ import annotations

import sys
from dataclasses import dataclass

import requests

# Flight category colour hints (used by renderers)
CATEGORY_COLORS = {
    "VFR":  (0, 220, 60),    # green
    "MVFR": (80, 120, 255),  # blue
    "IFR":  (220, 40, 40),   # red
    "LIFR": (180, 0, 200),   # magenta
}


@dataclass
class Metar:
    raw: str              # raw METAR string
    station: str          # ICAO e.g. "VOBL"
    wind_dir: int | None  # degrees, None = variable
    wind_spd: int | None  # knots
    wind_gust: int | None # knots, None if no gust
    visibility: str       # e.g. "9999" or "3000"
    temp_c: int | None
    dewpoint_c: int | None
    altimeter: str        # e.g. "Q1013"
    wx: str               # significant weather string e.g. "-RA" or ""
    sky: str              # highest ceiling or "CLR"
    category: str         # VFR / MVFR / IFR / LIFR

    def wind_str(self) -> str:
        if self.wind_dir is None:
            dir_s = "VRB"
        else:
            dir_s = f"{self.wind_dir:03d}"
        spd = self.wind_spd if self.wind_spd is not None else 0
        if self.wind_gust is not None:
            return f"{dir_s}/{spd}G{self.wind_gust}kt"
        return f"{dir_s}/{spd}kt"

    def temp_str(self) -> str:
        if self.temp_c is None:
            return "---"
        dew = f"/{self.dewpoint_c}" if self.dewpoint_c is not None else ""
        return f"{self.temp_c}{dew}°C"


_API = "https://aviationweather.gov/api/data/metar"


def fetch_metar(station: str) -> Metar | None:
    """
    Fetch latest METAR for station from aviationweather.gov.
    Returns None on any error.
    """
    try:
        resp = requests.get(
            _API,
            params={"ids": station, "format": "json", "taf": "false"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return _parse(data[0])
    except Exception as exc:
        print(f"[metar] fetch error: {exc}", file=sys.stderr)
        return None


def _parse(d: dict) -> Metar:
    wdir = d.get("wdir")
    wspd = d.get("wspd")
    wgst = d.get("wgst")

    # Wind dir can be "VRB"
    if isinstance(wdir, str) and wdir.upper() == "VRB":
        wind_dir = None
    else:
        wind_dir = int(wdir) if wdir is not None else None

    wind_spd  = int(wspd)  if wspd  is not None else None
    wind_gust = int(wgst)  if wgst  is not None else None

    temp   = d.get("temp")
    dewp   = d.get("dewp")
    temp_c = int(round(float(temp))) if temp is not None else None
    dewp_c = int(round(float(dewp))) if dewp is not None else None

    # Altimeter: prefer QNH (hPa) if available
    altim = d.get("altim")  # hPa
    if altim is not None:
        altimeter = f"Q{int(round(float(altim)))}"
    else:
        alts = d.get("altim")
        altimeter = str(alts) if alts else "----"

    vis = d.get("visib", "")
    wx  = d.get("wxString", "") or ""

    # Sky: pick lowest BKN/OVC or "CLR"
    sky_conds = d.get("skyCondition", []) or []
    ceiling = _ceiling(sky_conds)

    category = str(d.get("flightCategory", "VFR")).upper()

    return Metar(
        raw=str(d.get("rawOb", "")),
        station=str(d.get("stationId", "")),
        wind_dir=wind_dir,
        wind_spd=wind_spd,
        wind_gust=wind_gust,
        visibility=str(vis),
        temp_c=temp_c,
        dewpoint_c=dewp_c,
        altimeter=altimeter,
        wx=wx.strip(),
        sky=ceiling,
        category=category,
    )


def _ceiling(conditions: list[dict]) -> str:
    """Return the lowest BKN/OVC layer as 'BKN030', or 'CLR'."""
    for layer in conditions:
        cover = str(layer.get("skyCover", "")).upper()
        if cover in ("BKN", "OVC", "VV"):
            base = layer.get("cloudBase")
            if base is not None:
                return f"{cover}{int(base):03d}"
    return "CLR"
