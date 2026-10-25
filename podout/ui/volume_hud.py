import pygame

from podout.config import SCREEN_H, SCREEN_W, TOP_OFFSET, VOLUME_HUD_DURATION
from podout.resources import load_image


class UIVolumeHUD:
    """Overlay that briefly shows the volume level whenever it changes."""

    def __init__(self, playback):
        self.playback = playback
        self._last_volume = playback.volume
        self.time_left = 0.0

    def update(self, dt):
        if self.playback.volume != self._last_volume:
            self._last_volume = self.playback.volume
            self.time_left = VOLUME_HUD_DURATION
        else:
            self.time_left = max(0.0, self.time_left - dt)

    def draw(self, surface):
        if self.time_left <= 0:
            return
        bg = load_image("AlertBackgroundSmall")
        rect = bg.get_rect(center=(SCREEN_W // 2, TOP_OFFSET + (SCREEN_H - TOP_OFFSET) // 2))
        surface.blit(bg, rect)

        speaker = load_image("HighlightSpeaker")
        surface.blit(speaker, speaker.get_rect(center=(rect.centerx, rect.top + 50)))

        bar = pygame.Rect(rect.left + 30, rect.top + 100, rect.width - 60, 19)
        surface.blit(pygame.transform.scale(load_image("ProgressBarEmpty"), bar.size), bar)
        filled_w = round(bar.width * self.playback.volume)
        if filled_w > 0:
            surface.blit(pygame.transform.scale(load_image("ProgressBarFilled"), (filled_w, bar.height)), bar.topleft)
