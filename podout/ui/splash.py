import pygame

from podout import events, keys
from podout.config import SCREEN_H, SCREEN_W, TEXT_SECONDARY_COLOR, TOP_OFFSET
from podout.resources import get_font, load_image
from podout.ui.screen import UIScreen

SPLASH_FONT_SIZE = 24
SPLASH_TEXT_GAP = 20   # space between the image and the text below it


class UISplashScreen(UIScreen):
    """A centered splash image with optional text below it."""

    def __init__(self, image: str = "iPodExtraLarge", text: str = "Waiting for iPod",
                 title: str = "", dismissible: bool = False) -> None:
        super().__init__(title)
        self._image = image
        self._text = text
        self.dismissible = dismissible
        self._label: pygame.Surface | None = None   # cached rendered text, rebuilt when the values change

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, value: str) -> None:
        if value != self._image:
            self._image = value
            self.mark_dirty()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self.mark_dirty()

    def _rebuild(self) -> None:
        self._label = (get_font(SPLASH_FONT_SIZE).render(self._text, True, TEXT_SECONDARY_COLOR)
                       if self._text else None)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.dismissible and event.type == pygame.KEYDOWN and event.key in keys.BACK:
            events.pop_screen()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        self._ensure_built()

        img = load_image(self._image)
        block_h = img.get_height()
        if self._label:
            block_h += SPLASH_TEXT_GAP + self._label.get_height()

        # Center the image (and text) block within the area below the status bar.
        top = TOP_OFFSET + (SCREEN_H - TOP_OFFSET - block_h) // 2
        surface.blit(img, ((SCREEN_W - img.get_width()) // 2, top))
        if self._label:
            text_y = top + img.get_height() + SPLASH_TEXT_GAP
            surface.blit(self._label, ((SCREEN_W - self._label.get_width()) // 2, text_y))
