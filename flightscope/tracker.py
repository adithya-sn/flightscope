from __future__ import annotations

import sys
import time
from enum import Enum, auto

from .aircraft import Aircraft
from .config import AppConfig


class SelectionMode(Enum):
    AUTO = auto()    # always select nearest aircraft
    ROTATE = auto()  # cycle through aircraft on a timer
    LOCK = auto()    # hold current selection regardless of changes


class Tracker:
    def __init__(self, config: AppConfig) -> None:
        self._rotate_every = config.display.rotate_every
        self._registry: dict[str, Aircraft] = {}
        self._selected_icao: str | None = None
        self._mode: SelectionMode = SelectionMode.ROTATE
        self._last_rotate: float = 0.0
        self._rotate_order: list[str] = []  # stable ordered list for ROTATE mode

    @property
    def selected(self) -> Aircraft | None:
        if self._selected_icao is None:
            return None
        return self._registry.get(self._selected_icao)

    @property
    def mode(self) -> SelectionMode:
        return self._mode

    @property
    def aircraft(self) -> list[Aircraft]:
        """All tracked aircraft sorted by distance_km ascending."""
        return sorted(self._registry.values(), key=lambda a: a.distance_km)

    def update(self, aircraft: list[Aircraft]) -> None:
        """Ingest new aircraft list from datasource. Call once per poll cycle."""
        # Rebuild registry
        self._registry = {a.icao: a for a in aircraft}

        # Sync rotate_order: remove departed, append new arrivals
        current_icaos = set(self._registry)
        self._rotate_order = [icao for icao in self._rotate_order if icao in current_icaos]
        for a in aircraft:
            if a.icao not in self._rotate_order:
                self._rotate_order.append(a.icao)

        # Apply selection logic per mode
        if self._mode is SelectionMode.AUTO:
            self._select_nearest()
        elif self._mode is SelectionMode.ROTATE:
            self._maybe_rotate()
        elif self._mode is SelectionMode.LOCK:
            if self._selected_icao not in self._registry:
                print(
                    f"[tracker] locked aircraft {self._selected_icao!r} departed, reverting to AUTO",
                    file=sys.stderr,
                )
                self._mode = SelectionMode.AUTO
                self._select_nearest()

        # Final validation: ensure selected_icao is actually in registry
        if self._selected_icao not in self._registry:
            self._selected_icao = self._rotate_order[0] if self._rotate_order else None

    def set_mode(self, mode: SelectionMode) -> None:
        self._mode = mode
        if mode is SelectionMode.AUTO:
            self._select_nearest()

    def lock(self, icao: str) -> None:
        """Lock selection to a specific aircraft by ICAO hex."""
        self._selected_icao = icao
        self._mode = SelectionMode.LOCK

    def next(self) -> None:
        """Manually advance to the next aircraft; switches to ROTATE mode."""
        self._mode = SelectionMode.ROTATE
        self._advance_rotate()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_nearest(self) -> None:
        self._selected_icao = self._rotate_order[0] if self._rotate_order else None

    def _maybe_rotate(self) -> None:
        if not self._rotate_order:
            self._selected_icao = None
            return
        if self._selected_icao is None:
            self._selected_icao = self._rotate_order[0]
            self._last_rotate = time.time()
            return
        if time.time() - self._last_rotate >= self._rotate_every:
            self._advance_rotate()

    def _advance_rotate(self) -> None:
        if not self._rotate_order:
            self._selected_icao = None
            return
        if self._selected_icao in self._rotate_order:
            idx = self._rotate_order.index(self._selected_icao)
            self._selected_icao = self._rotate_order[(idx + 1) % len(self._rotate_order)]
        else:
            self._selected_icao = self._rotate_order[0]
        self._last_rotate = time.time()
