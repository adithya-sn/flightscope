from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class DisplayBackend(ABC):
    """
    Abstract display backend.

    Subclasses declare PANEL_WIDTH / PANEL_HEIGHT / IMAGE_MODE.
    The main loop calls new_canvas() each frame, draws into the returned
    images, then calls show() to push them to the physical display.
    """

    # Dimensions of each logical panel (radar / info) in pixels.
    # Subclasses must override these.
    PANEL_WIDTH: int = 128
    PANEL_HEIGHT: int = 64

    # PIL image mode: "1" for 1-bit OLEDs, "RGB" for colour TFT/pygame.
    IMAGE_MODE: str = "1"

    # Colour palette used by renderers (RGB tuples).
    # Subclasses override to set the look.
    COLOR_BG: tuple[int, int, int] = (0, 0, 0)
    COLOR_FG: tuple[int, int, int] = (255, 255, 255)
    COLOR_ACCENT: tuple[int, int, int] = (255, 255, 255)  # selected aircraft

    @abstractmethod
    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        """
        Push both rendered images to their respective displays.
        radar_image → left panel (radar).
        info_image  → right panel (info).
        Images are PANEL_WIDTH × PANEL_HEIGHT, mode IMAGE_MODE.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Release hardware resources. Called on shutdown."""
        ...

    def new_canvas(self) -> tuple[Image.Image, Image.Image]:
        """Create a fresh black image pair for one frame."""
        size = (self.PANEL_WIDTH, self.PANEL_HEIGHT)
        radar = Image.new(self.IMAGE_MODE, size)
        info = Image.new(self.IMAGE_MODE, size)
        return radar, info

    def fill_color(self) -> int | tuple[int, int, int]:
        """Foreground fill value appropriate for IMAGE_MODE."""
        return self.COLOR_FG if self.IMAGE_MODE == "RGB" else 1
