from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .aircraft import Aircraft
from .tracker import SelectionMode

_font = ImageFont.load_default()

_MODE_LABELS = {
    SelectionMode.AUTO:   "[AUTO]",
    SelectionMode.ROTATE: "[ROT]",
    SelectionMode.LOCK:   "[LOCK]",
}

# Layout constants
_CALLSIGN_SCALE = 2   # callsign rendered at 2× then pasted
_DATA_Y = 20          # y where two-column data rows begin
_COL_R = 66           # x of right column


def draw_info(img: Image.Image, aircraft: Aircraft | None, mode: SelectionMode) -> None:
    """
    Draw info display onto img (128×64, 1-bit).
    Pure function — no I/O, no state. Modifies img in place.

    Layout:
      [ 0–17]  Callsign at 2× scale
      [18]     Thin separator line
      [20–29]  Left: ALT + vrate    Right: SPD
      [31–40]  Left: DST            Right: HDG
      [52]     Mode indicator (right-aligned)
    """
    canvas = ImageDraw.Draw(img)
    mode_label = _MODE_LABELS[mode]

    if aircraft is None:
        canvas.text((20, 24), "NO AIRCRAFT", font=_font, fill=1)
        _draw_mode(canvas, mode_label)
        return

    # --- Callsign at 2× ---
    _paste_scaled_text(img, (0, 0), aircraft.display_callsign(), scale=_CALLSIGN_SCALE)

    # Separator line under callsign
    canvas.line((0, 18, 127, 18), fill=1)

    # --- Two-column data rows ---
    # Left: ALT (with vrate symbol), DST
    canvas.text((0, _DATA_Y),      f"ALT {aircraft.altitude_str()} {aircraft.vrate_symbol()}", font=_font, fill=1)
    canvas.text((0, _DATA_Y + 11), f"DST {aircraft.distance_km:.1f}km", font=_font, fill=1)

    # Right: SPD, HDG
    canvas.text((_COL_R, _DATA_Y),      f"SPD {aircraft.speed_str()}", font=_font, fill=1)
    hdg = f"HDG {aircraft.track:.0f}\u00b0" if aircraft.track is not None else "HDG ---"
    canvas.text((_COL_R, _DATA_Y + 11), hdg, font=_font, fill=1)

    _draw_mode(canvas, mode_label)


def _paste_scaled_text(img: Image.Image, pos: tuple[int, int], text: str, scale: int) -> None:
    """Render text at scale× size and paste it onto img."""
    # Measure at 1×
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    bbox = probe.textbbox((0, 0), text, font=_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if w <= 0 or h <= 0:
        return

    # Draw at 1× on a tight canvas, correcting for bbox top offset
    small = Image.new("1", (w, h))
    ImageDraw.Draw(small).text((0, -bbox[1]), text, font=_font, fill=1)

    # Scale up with nearest-neighbour (sharp pixels)
    big = small.resize((w * scale, h * scale), resample=Image.NEAREST)

    # Paste — for mode "1" images, PIL paste works directly
    img.paste(big, pos)


def _draw_mode(canvas: ImageDraw.ImageDraw, label: str) -> None:
    """Right-align mode label at the bottom of the display."""
    bbox = canvas.textbbox((0, 0), label, font=_font)
    text_w = bbox[2] - bbox[0]
    x = 128 - text_w
    canvas.text((max(0, x), 52), label, font=_font, fill=1)
