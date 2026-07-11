from __future__ import annotations

from PIL import Image

from .config import AppConfig
from .display import DisplayBackend


class OledBackend(DisplayBackend):
    """luma.oled SSD1306 backend for the physical Raspberry Pi hardware."""

    PANEL_WIDTH = 128
    PANEL_HEIGHT = 64
    IMAGE_MODE = "1"
    COLOR_FG = 1
    COLOR_ACCENT = 1

    def __init__(self, config: AppConfig) -> None:
        # Deferred imports — luma.oled only available on Pi
        from luma.core.interface.serial import spi
        from luma.oled.device import ssd1306

        serial_radar = spi(
            port=config.oled.radar_spi_port,
            device=config.oled.radar_spi_device,
            gpio_DC=config.oled.radar_dc,
            gpio_RST=config.oled.radar_rst,
        )
        self._radar_dev = ssd1306(serial_radar)

        serial_info = spi(
            port=config.oled.info_spi_port,
            device=config.oled.info_spi_device,
            gpio_DC=config.oled.info_dc,
            gpio_RST=config.oled.info_rst,
        )
        self._info_dev = ssd1306(serial_info)

    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        self._radar_dev.display(radar_image)
        self._info_dev.display(info_image)

    def close(self) -> None:
        self._radar_dev.cleanup()
        self._info_dev.cleanup()
