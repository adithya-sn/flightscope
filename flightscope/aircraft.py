from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Aircraft:
    icao: str                       # ICAO hex — primary key, never use list index
    callsign: str                   # flight callsign; empty string if unknown
    lat: float
    lon: float
    altitude: int | None            # feet above sea level; 0 = on ground; None = unknown
    speed: float | None             # knots ground speed; None = unknown
    track: float | None             # degrees true (0–360); None = not reported
    vertical_rate: int | None       # ft/min; positive = climbing; None = unknown
    distance_km: float = field(default=0.0)  # set by datasource after Haversine
    bearing_deg: float = field(default=0.0)  # set by datasource after bearing calc

    def display_callsign(self) -> str:
        """Callsign if non-empty, else ICAO hex uppercased."""
        cs = self.callsign.strip()
        return cs.upper() if cs else self.icao.upper()

    def altitude_str(self) -> str:
        if self.altitude is None:
            return "--- ft"
        return f"{self.altitude:,} ft"

    def speed_str(self) -> str:
        if self.speed is None:
            return "--- kt"
        return f"{int(self.speed)} kt"

    def vrate_symbol(self) -> str:
        """'↑' climbing, '↓' descending, '→' level or unknown."""
        if self.vertical_rate is None or abs(self.vertical_rate) < 64:
            return "\u2192"
        return "\u2191" if self.vertical_rate > 0 else "\u2193"
