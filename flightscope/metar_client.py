from __future__ import annotations

import threading
import time

from .metar import Metar, fetch_metar

_POLL_INTERVAL = 30 * 60  # 30 minutes — METARs update every 30 min
_FIRST_FETCH_DELAY = 0.5  # fetch almost immediately on startup


class MetarClient:
    """
    Background-thread METAR poller. Thread-safe read via .latest property.
    """

    def __init__(self, station: str) -> None:
        self._station = station
        self._latest: Metar | None = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @property
    def latest(self) -> Metar | None:
        with self._lock:
            return self._latest

    def _run(self) -> None:
        time.sleep(_FIRST_FETCH_DELAY)
        while True:
            metar = fetch_metar(self._station)
            if metar is not None:
                with self._lock:
                    self._latest = metar
            time.sleep(_POLL_INTERVAL)
