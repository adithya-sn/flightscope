from __future__ import annotations

from PIL import Image

from .config import AppConfig
from .display import DisplayBackend


class TftBackend(DisplayBackend):
    """
    ILI9488 480×320 SPI TFT backend via luma.lcd.

    The two 240×320 logical panels (radar left, info right) are
    composited into a single 480×320 RGB image and pushed in one shot.
    """

    IMAGE_MODE = "RGB"
    COLOR_BG = (0, 0, 0)
    COLOR_FG = (0, 220, 60)       # phosphor green
    COLOR_ACCENT = (255, 220, 0)  # amber for selected aircraft

    def __init__(self, config: AppConfig) -> None:
        self.PANEL_WIDTH = config.tft.width // 2
        self.PANEL_HEIGHT = config.tft.height
        self._full_width = config.tft.width
        self._full_height = config.tft.height

        # Deferred import — luma.lcd only available on Pi
        from luma.core.interface.serial import spi
        from luma.lcd.device import ili9488

        serial = spi(
            port=config.tft.spi_port,
            device=config.tft.spi_device,
            gpio_DC=config.tft.dc,
            gpio_RST=config.tft.rst,
        )
        self._device = ili9488(serial, width=config.tft.width, height=config.tft.height)

    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        combined = Image.new("RGB", (self._full_width, self._full_height))
        combined.paste(radar_image, (0, 0))
        combined.paste(info_image, (self.PANEL_WIDTH, 0))
        self._device.display(combined)

    def close(self) -> None:
        self._device.cleanup()
