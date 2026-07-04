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
class AppConfig:
    source: SourceConfig
    observer: ObserverConfig
    display: DisplayConfig
    oled: OledConfig


_DEFAULT_OLED = OledConfig(
    radar_dc=0, radar_rst=0, radar_spi_port=0, radar_spi_device=0,
    info_dc=0,  info_rst=0,  info_spi_port=0,  info_spi_device=0,
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
    if backend not in {"oled", "pygame"}:
        raise ValueError(f"display.backend must be 'oled' or 'pygame', got {backend!r}")

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
    )
