from __future__ import annotations

import sys

from PIL import Image

from .display import DisplayBackend


class PygameBackend(DisplayBackend):
    """Desktop development backend. Shows both OLEDs side-by-side in a pygame window."""

    SCALE: int = 3   # each OLED pixel → 3×3 screen pixels
    GAP: int = 8     # pixel gap between the two panels

    def __init__(self) -> None:
        import pygame  # deferred import — only required when this backend is used

        self._pygame = pygame
        pygame.init()
        win_w = self.WIDTH * self.SCALE * 2 + self.GAP
        win_h = self.HEIGHT * self.SCALE
        self._screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption("FlightScope — Dev Mode")

    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        pygame = self._pygame

        # Handle window close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                sys.exit(0)

        self._screen.fill((20, 20, 20))  # dark grey background

        # Blit separator line
        panel_w = self.WIDTH * self.SCALE
        sep_x = panel_w + self.GAP // 2
        pygame.draw.line(
            self._screen, (60, 60, 60), (sep_x, 0), (sep_x, self.HEIGHT * self.SCALE)
        )

        # Convert and blit radar panel (left)
        radar_surf = self._pil_to_surface(radar_image)
        self._screen.blit(radar_surf, (0, 0))

        # Convert and blit info panel (right)
        info_surf = self._pil_to_surface(info_image)
        self._screen.blit(info_surf, (panel_w + self.GAP, 0))

        pygame.display.flip()

    def close(self) -> None:
        self._pygame.quit()

    def _pil_to_surface(self, img: Image.Image):
        pygame = self._pygame
        rgb = img.convert("RGB")
        # Scale up before converting to avoid double-copy
        scaled = rgb.resize(
            (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE),
            resample=Image.NEAREST,
        )
        return pygame.image.fromstring(scaled.tobytes(), scaled.size, "RGB")
