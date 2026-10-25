import pygame

from podout import events
from podout.config import SCREEN_W, TEXT_COLOR, TEXT_SECONDARY_COLOR
from podout.resources import get_font, load_image
from podout.ui.screen import UIScreen

ART_POS = (30, 80)
INFO_X = 300
BAR_RECT = pygame.Rect(INFO_X, 350, SCREEN_W - INFO_X - 30, 19)


def _fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


class UINowPlaying(UIScreen):
    def __init__(self, playback):
        super().__init__("Now Playing")
        self.playback = playback

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_SPACE:
            self.playback.toggle()
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            events.pop_screen()
        else:
            return False
        return True

    def draw(self, surface):
        pb = self.playback
        surface.blit(load_image(pb.artwork), ART_POS)

        y = 110
        max_w = SCREEN_W - INFO_X - 30
        for text, size, color in ((pb.title, 30, TEXT_COLOR),
                                  (pb.artist, 24, TEXT_SECONDARY_COLOR),
                                  (pb.album, 24, TEXT_SECONDARY_COLOR)):
            label = get_font(size).render(text, True, color)
            surface.blit(label, (INFO_X, y), pygame.Rect(0, 0, min(label.get_width(), max_w), label.get_height()))
            y += label.get_height() + 12

        state = load_image("Play40" if pb.playing else "Pause40")
        surface.blit(state, (INFO_X, BAR_RECT.top - state.get_height() - 16))

        surface.blit(pygame.transform.scale(load_image("ProgressBarEmpty"), BAR_RECT.size), BAR_RECT)
        frac = pb.position / pb.duration if pb.duration > 0 else 0
        filled_w = int(BAR_RECT.width * frac)
        if filled_w > 0:
            filled = pygame.transform.scale(load_image("ProgressBarFilled"), (filled_w, BAR_RECT.height))
            surface.blit(filled, BAR_RECT.topleft)

        font = get_font(20, bold=False)
        elapsed = font.render(_fmt_time(pb.position), True, TEXT_SECONDARY_COLOR)
        remaining = font.render("-" + _fmt_time(pb.duration - pb.position), True, TEXT_SECONDARY_COLOR)
        surface.blit(elapsed, (BAR_RECT.left, BAR_RECT.bottom + 8))
        surface.blit(remaining, (BAR_RECT.right - remaining.get_width(), BAR_RECT.bottom + 8))
