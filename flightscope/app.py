from __future__ import annotations

import argparse
import sys
import time

from PIL import ImageDraw

from .config import load_config
from .datasource import Dump1090Client
from .display import DisplayBackend
from .mock_datasource import MockDatasource
from .info import draw_info
from .radar import draw_radar
from .tracker import Tracker


def _make_backend(config) -> DisplayBackend:
    if config.display.backend == "oled":
        from .oled_backend import OledBackend
        return OledBackend(config)
    elif config.display.backend == "pygame":
        from .pygame_backend import PygameBackend
        return PygameBackend()
    else:
        print(f"[app] unknown backend: {config.display.backend!r}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="FlightScope ADS-B Radar")
    parser.add_argument(
        "--config",
        default="config.toml",
        metavar="PATH",
        help="path to config.toml (default: config.toml)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="use mock datasource (no dump1090 required)",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"[app] config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError) as exc:
        print(f"[app] config error: {exc}", file=sys.stderr)
        sys.exit(1)

    backend = _make_backend(config)
    client = MockDatasource(config) if args.mock else Dump1090Client(config)
    tracker = Tracker(config)

    frame_interval = 1.0 / config.display.fps   # e.g. 1/15 ≈ 0.0667 s
    poll_interval = config.source.poll_interval  # e.g. 1.0 s
    last_poll: float = 0.0

    print(
        f"[app] starting — backend={config.display.backend} "
        f"fps={config.display.fps} poll={poll_interval}s"
        + (" [MOCK]" if args.mock else ""),
        file=sys.stderr,
    )

    try:
        while True:
            loop_start = time.monotonic()

            # Poll datasource at configured interval (decoupled from render rate)
            now = time.monotonic()
            if now - last_poll >= poll_interval:
                fetch_start = time.monotonic()
                aircraft = client.fetch()
                fetch_elapsed = time.monotonic() - fetch_start
                if fetch_elapsed > 0.5:
                    print(
                        f"[app] slow fetch: {fetch_elapsed:.2f}s",
                        file=sys.stderr,
                    )
                tracker.update(aircraft)
                last_poll = now

            # Render frame
            radar_img, info_img = backend.new_canvas()
            draw_radar(ImageDraw.Draw(radar_img), tracker.aircraft, tracker.selected, config)
            draw_info(info_img, tracker.selected, tracker.mode)

            try:
                backend.show(radar_img, info_img)
            except Exception as exc:
                print(f"[app] display error: {exc}", file=sys.stderr)

            # Sleep to hit target frame rate
            elapsed = time.monotonic() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        backend.close()


if __name__ == "__main__":
    main()
