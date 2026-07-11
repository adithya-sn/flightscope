from __future__ import annotations

import sys

from PIL import Image

from .config import AppConfig
from .display import DisplayBackend


class PygameBackend(DisplayBackend):
    """
    Desktop development backend. Simulates the TFT — two panels side-by-side
    in a single pygame window. Matches TFT colors and dimensions so dev output
    is representative of hardware.
    """

    IMAGE_MODE = "RGB"
    COLOR_BG = (0, 0, 0)
    COLOR_FG = (0, 220, 60)       # phosphor green (matches TftBackend)
    COLOR_ACCENT = (255, 220, 0)  # amber for selected aircraft

    SCALE: int = 1   # set >1 to magnify on HiDPI screens
    GAP: int = 2     # px gap between panels

    def __init__(self, config: AppConfig) -> None:
        self.PANEL_WIDTH = config.tft.width // 2
        self.PANEL_HEIGHT = config.tft.height
        self._full_width = config.tft.width
        self._full_height = config.tft.height

        import pygame  # deferred
        self._pygame = pygame
        pygame.init()
        win_w = self._full_width * self.SCALE + self.GAP
        win_h = self._full_height * self.SCALE
        self._screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption("FlightScope — Dev Mode")

    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        pygame = self._pygame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                sys.exit(0)

        self._screen.fill((10, 10, 10))

        # Separator
        sep_x = self.PANEL_WIDTH * self.SCALE + self.GAP // 2
        pygame.draw.line(
            self._screen, (40, 40, 40),
            (sep_x, 0), (sep_x, self._full_height * self.SCALE),
        )

        self._screen.blit(self._to_surface(radar_image), (0, 0))
        self._screen.blit(self._to_surface(info_image), (self.PANEL_WIDTH * self.SCALE + self.GAP, 0))
        pygame.display.flip()

    def close(self) -> None:
        self._pygame.quit()

    def _to_surface(self, img: Image.Image):
        pygame = self._pygame
        if self.SCALE != 1:
            img = img.resize(
                (img.width * self.SCALE, img.height * self.SCALE),
                resample=Image.NEAREST,
            )
        rgb = img.convert("RGB")
        return pygame.image.fromstring(rgb.tobytes(), rgb.size, "RGB")
