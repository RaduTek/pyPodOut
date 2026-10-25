import pygame

from podout.config import (SCREEN_W, STATUS_BAR_FONT_SIZE, STATUS_BAR_HEIGHT,
                           STATUS_BAR_MARGIN_X, TEXT_HIGHLIGHT_COLOR)
from podout.playback import Playback
from podout.resources import get_font, load_image


class UIStatusBar:
    """Top bar showing the current screen title and the playback state."""

    def __init__(self, playback: Playback) -> None:
        self.playback = playback
        self.rect = pygame.Rect(0, 0, SCREEN_W, STATUS_BAR_HEIGHT)

    def draw(self, surface: pygame.Surface, title: str) -> None:
        surface.blit(load_image("StatusBarBackground"), self.rect)
        center_y = self.rect.centery

        reserved = 0
        if self.playback.has_track:
            icon = load_image("Play40" if self.playback.playing else "Pause40")
            icon_x = self.rect.right - STATUS_BAR_MARGIN_X - icon.get_width()
            surface.blit(icon, (icon_x, center_y - icon.get_height() // 2))
            reserved = icon.get_width() + STATUS_BAR_MARGIN_X

        label = get_font(STATUS_BAR_FONT_SIZE).render(title, True, TEXT_HIGHLIGHT_COLOR)
        # Centered, but kept clear of the playback icon on both sides.
        max_w = self.rect.width - 2 * (reserved + STATUS_BAR_MARGIN_X)
        w = min(label.get_width(), max_w)
        surface.blit(label, (self.rect.centerx - w // 2, center_y - label.get_height() // 2),
                     pygame.Rect(0, 0, w, label.get_height()))
