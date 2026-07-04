from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class DisplayBackend(ABC):
    """Abstract display backend. Manages two 128×64 1-bit surfaces."""

    WIDTH: int = 128
    HEIGHT: int = 64

    @abstractmethod
    def show(self, radar_image: Image.Image, info_image: Image.Image) -> None:
        """
        Push both rendered images to their respective physical displays.
        radar_image → left display (radar).
        info_image  → right display (info panel).
        Both images must be 128×64, mode "1" (1-bit).
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Release hardware resources. Called on shutdown."""
        ...

    def new_canvas(self) -> tuple[Image.Image, Image.Image]:
        """Create fresh blank (black) image pair for one frame."""
        radar = Image.new("1", (self.WIDTH, self.HEIGHT))
        info = Image.new("1", (self.WIDTH, self.HEIGHT))
        return radar, info
