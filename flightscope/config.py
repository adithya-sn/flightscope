from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceConfig:
    url: str
    poll_interval: float


@dataclass(frozen=True)
class ObserverConfig:
    lat: float
    lon: float
    range_km: float


@dataclass(frozen=True)
class DisplayConfig:
    backend: str
    fps: int
    rotate_every: float


@dataclass(frozen=True)
class OledConfig:
    radar_dc: int
    radar_rst: int
    radar_spi_port: int
    radar_spi_device: int
    info_dc: int
    info_rst: int
    info_spi_port: int
    info_spi_device: int


@dataclass(frozen=True)
class MetarConfig:
    station: str
    enabled: bool


@dataclass(frozen=True)
class TftConfig:
    dc: int
    rst: int
    spi_port: int
    spi_device: int
    width: int   # physical pixels (480 for ILI9488 landscape)
    height: int  # physical pixels (320 for ILI9488 landscape)


@dataclass(frozen=True)
class AppConfig:
    source: SourceConfig
    observer: ObserverConfig
    display: DisplayConfig
    oled: OledConfig
    tft: TftConfig
    metar: MetarConfig


_DEFAULT_OLED = OledConfig(
    radar_dc=0, radar_rst=0, radar_spi_port=0, radar_spi_device=0,
    info_dc=0,  info_rst=0,  info_spi_port=0,  info_spi_device=0,
)

_DEFAULT_METAR = MetarConfig(station="VOBL", enabled=True)

_DEFAULT_TFT = TftConfig(
    dc=0, rst=0, spi_port=0, spi_device=0, width=480, height=320,
)


def load_config(path: str | Path = "config.toml") -> AppConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    src = raw["source"]
    obs = raw["observer"]
    dsp = raw["display"]

    fps = int(dsp["fps"])
    if not (1 <= fps <= 60):
        raise ValueError(f"display.fps must be 1–60, got {fps}")

    range_km = float(obs["range_km"])
    if range_km <= 0:
        raise ValueError(f"observer.range_km must be > 0, got {range_km}")

    backend = str(dsp["backend"])
    if backend not in {"oled", "tft", "pygame"}:
        raise ValueError(f"display.backend must be 'oled', 'tft', or 'pygame', got {backend!r}")

    if "oled" in raw:
        o = raw["oled"]
        oled_cfg = OledConfig(
            radar_dc=int(o["radar_dc"]),
            radar_rst=int(o["radar_rst"]),
            radar_spi_port=int(o["radar_spi_port"]),
            radar_spi_device=int(o["radar_spi_device"]),
            info_dc=int(o["info_dc"]),
            info_rst=int(o["info_rst"]),
            info_spi_port=int(o["info_spi_port"]),
            info_spi_device=int(o["info_spi_device"]),
        )
    else:
        oled_cfg = _DEFAULT_OLED

    if "tft" in raw:
        t = raw["tft"]
        tft_cfg = TftConfig(
            dc=int(t["dc"]),
            rst=int(t["rst"]),
            spi_port=int(t["spi_port"]),
            spi_device=int(t["spi_device"]),
            width=int(t.get("width", 480)),
            height=int(t.get("height", 320)),
        )
    else:
        tft_cfg = _DEFAULT_TFT

    if "metar" in raw:
        m = raw["metar"]
        metar_cfg = MetarConfig(
            station=str(m.get("station", "VOBL")).upper(),
            enabled=bool(m.get("enabled", True)),
        )
    else:
        metar_cfg = _DEFAULT_METAR

    return AppConfig(
        source=SourceConfig(
            url=str(src["url"]),
            poll_interval=float(src["poll_interval"]),
        ),
        observer=ObserverConfig(
            lat=float(obs["lat"]),
            lon=float(obs["lon"]),
            range_km=range_km,
        ),
        display=DisplayConfig(
            backend=backend,
            fps=fps,
            rotate_every=float(dsp["rotate_every"]),
        ),
        oled=oled_cfg,
        tft=tft_cfg,
        metar=metar_cfg,
    )
