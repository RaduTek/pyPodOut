import math

import pygame

from podout import events, keys
from podout.config import SCREEN_H, SCREEN_W, TEXT_COLOR, TEXT_SECONDARY_COLOR, TOP_OFFSET
from podout.playback import Playback
from podout.resources import get_font, load_image
from podout.ui.screen import UIScreen
from podout.ui.text import Marquee, draw_text

CONTENT_MARGIN = 35          # left/right inset of the screen content
ART_POS = (30, 90)
COVER_SIZE = 240             # fixed on-screen size of the (un-turned) cover art, any source
COVER_ANGLE = 8             # degrees the cover is turned about its vertical axis (facing right)
REFLECTION_FRACTION = 3      # reflection height = artwork height / this
COVER_SUPERSAMPLE = 3        # warp at this multiple then shrink, to antialias the turned edges
INFO_X = 300
INFO_TOP = 130               # top of the text block (nudged down from the artwork line)
LINE_GAP = 12                # vertical gap between text lines
RATING_GAP = 4               # gap between rating glyphs
MODE_ICON_MARGIN = 8         # gap between the mode icons and the right edge of the screen
MODE_ICON_GAP = 8            # gap between the shuffle/repeat icons
BAR_HEIGHT = 21
BAR_BOTTOM_MARGIN = 40       # gap below the progress bar
TIME_GAP = 12                # gap between a time label and the progress bar
TIME_OFFSET_Y = 2


def _fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


class UINowPlaying(UIScreen):
    def __init__(self, playback: Playback) -> None:
        super().__init__("Now Playing")
        self.playback = playback
        self._title_marquee = Marquee()   # the title scrolls when it overflows
        self._title = ""
        self._covers: dict[str, pygame.Surface] = {}   # artwork name -> cached turned cover + reflection

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Play/pause, next/previous and volume are handled globally in main.py.
        if event.type == pygame.KEYDOWN and event.key in keys.BACK:
            events.pop_screen()
            return True
        return False

    def update(self, dt: float) -> None:
        if self.playback.title != self._title:
            # New track: restart the title scroll from the beginning.
            self._title = self.playback.title
            self._title_marquee.reset()
        self._title_marquee.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        pb = self.playback

        cover = self._cover(pb.artwork)
        # Bottom-anchor where the un-warped reflection ended, and center on the
        # cover's fixed footprint; the turned cover grows upward from there.
        baseline = ART_POS[1] + COVER_SIZE + COVER_SIZE // REFLECTION_FRACTION
        x = ART_POS[0] + COVER_SIZE // 2 - cover.get_width() // 2
        surface.blit(cover, (x, baseline - cover.get_height()))

        self._draw_mode_icons(surface)
        self._draw_info(surface)
        self._draw_progress(surface)

    def _draw_info(self, surface: pygame.Surface) -> None:
        pb = self.playback
        y = INFO_TOP
        max_w = SCREEN_W - INFO_X - CONTENT_MARGIN
        # Only the title scrolls; artist, album and the counter are ellipsized.
        for text, size, color, marquee in ((pb.title, 30, TEXT_COLOR, self._title_marquee),
                                           (pb.artist, 24, TEXT_SECONDARY_COLOR, None),
                                           (pb.album, 24, TEXT_SECONDARY_COLOR, None),
                                           (f"{pb.index + 1} of {len(pb.queue)}", 20,
                                            TEXT_SECONDARY_COLOR, None)):
            font = get_font(size)
            render = lambda t, f=font, c=color: f.render(t, True, c)
            h = font.get_height()
            draw_text(surface, render, text, INFO_X, y + h // 2, max_w, marquee)
            y += h + LINE_GAP

        self._draw_rating(surface, INFO_X, y + RATING_GAP)

    def _draw_rating(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Draw five glyphs: `rating` stars (1..5) then dots for the remainder."""
        rating = self.playback.rating
        if not 1 <= rating <= 5:
            return
        star, dot = load_image("RatingStar"), load_image("RatingDot")
        for i in range(5):
            glyph = star if i < rating else dot
            surface.blit(glyph, (x + i * (glyph.get_width() + RATING_GAP), y))

    def _draw_mode_icons(self, surface: pygame.Surface) -> None:
        """Shuffle and/or repeat icons in the top-right of the content area."""
        pb = self.playback
        names = []
        if pb.shuffle:
            names.append("Shuffle40")
        if pb.repeat == "one":
            names.append("RepeatOne40")
        elif pb.repeat == "all":
            names.append("RepeatAll40")

        x = SCREEN_W - MODE_ICON_MARGIN   # right edge; icons laid out right to left
        y = TOP_OFFSET + MODE_ICON_GAP
        for name in reversed(names):
            icon = load_image(name)
            x -= icon.get_width()
            surface.blit(icon, (x, y))
            x -= MODE_ICON_GAP

    def _draw_progress(self, surface: pygame.Surface) -> None:
        pb = self.playback
        font = get_font(20, bold=False)
        elapsed = font.render(_fmt_time(pb.position), True, TEXT_SECONDARY_COLOR)
        remaining = font.render("-" + _fmt_time(pb.duration - pb.position), True, TEXT_SECONDARY_COLOR)

        center_y = SCREEN_H - BAR_BOTTOM_MARGIN - BAR_HEIGHT // 2
        text_center_y = center_y + TIME_OFFSET_Y
        left = CONTENT_MARGIN
        right = SCREEN_W - CONTENT_MARGIN
        # Time labels flank the bar; the bar fills the space between them.
        surface.blit(elapsed, (left, text_center_y - elapsed.get_height() // 2))
        surface.blit(remaining, (right - remaining.get_width(), text_center_y - remaining.get_height() // 2))

        bar_left = left + elapsed.get_width() + TIME_GAP
        bar_right = right - remaining.get_width() - TIME_GAP
        bar = pygame.Rect(bar_left, center_y - BAR_HEIGHT // 2, max(0, bar_right - bar_left), BAR_HEIGHT)
        surface.blit(pygame.transform.scale(load_image("ProgressBarEmpty"), bar.size), bar)
        frac = pb.position / pb.duration if pb.duration > 0 else 0
        filled_w = int(bar.width * frac)
        if filled_w > 0:
            filled = pygame.transform.scale(load_image("ProgressBarFilled"), (filled_w, BAR_HEIGHT))
            surface.blit(filled, bar.topleft)

    def _cover(self, name: str) -> pygame.Surface:
        """The artwork with its reflection, turned about the vertical axis so it
        faces slightly to the right (as the iPod classic Now Playing does)."""
        cover = self._covers.get(name)
        if cover is None:
            art = load_image(name)
            # Normalize any source to the fixed cover footprint.
            if art.get_size() != (COVER_SIZE, COVER_SIZE):
                art = pygame.transform.smoothscale(art, (COVER_SIZE, COVER_SIZE))
            w, h = art.get_size()
            rh = h // REFLECTION_FRACTION

            # Reflection: the top slice of the vertically flipped artwork, fading out.
            reflection = pygame.transform.flip(art, False, True).subsurface((0, 0, w, rh)).copy()
            fade = pygame.Surface((w, rh), pygame.SRCALPHA)
            for row in range(rh):
                alpha = int(110 * (1 - row / rh))   # strongest at the contact edge, fading to 0
                fade.fill((255, 255, 255, alpha), pygame.Rect(0, row, w, 1))
            reflection.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Warp the artwork and reflection together so they stay a single plane.
            combined = pygame.Surface((w, h + rh), pygame.SRCALPHA)
            combined.blit(art, (0, 0))
            combined.blit(reflection, (0, h))
            cover = self._rotate_y(combined, COVER_ANGLE)
            self._covers[name] = cover
        return cover

    @staticmethod
    def _rotate_y(src: pygame.Surface, angle_deg: float,
                  supersample: int = COVER_SUPERSAMPLE) -> pygame.Surface:
        """Perspective-project `src` as if rotated about its vertical axis.

        Each source column becomes a vertical column in the result, scaled and
        placed by a one-point projection: a positive angle turns the plane to
        face right, so its left edge comes nearer (taller) and its right recedes.

        The warp point-samples, so it is run at `supersample`x resolution and
        smoothscaled back down to antialias the turned edges and the content.
        """
        if supersample > 1:
            w, h = src.get_size()
            hi = pygame.transform.smoothscale(src, (w * supersample, h * supersample))
            warped = UINowPlaying._rotate_y(hi, angle_deg, supersample=1)
            target = (max(1, round(warped.get_width() / supersample)),
                      max(1, round(warped.get_height() / supersample)))
            return pygame.transform.smoothscale(warped, target)

        w, h = src.get_size()
        theta = math.radians(angle_deg)
        sin, cos = math.sin(theta), math.cos(theta)
        depth = 2.0 * w          # camera distance; focal length == depth so angle 0 is identity
        half = w / 2.0

        def screen_x(x: float) -> float:     # project model x in [-half, half]
            return x * cos * depth / (depth + x * sin)

        def scale_at(x: float) -> float:     # foreshortening of the column at model x
            return depth / (depth + x * sin)

        left, right = screen_x(-half), screen_x(half)
        out_w = max(1, math.ceil(right - left))
        out_h = max(1, math.ceil(h * max(scale_at(-half), scale_at(half))))
        out = pygame.Surface((out_w, out_h), pygame.SRCALPHA)
        mid_y = out_h / 2.0

        for dx in range(out_w):
            sx = dx + left
            # Invert screen_x to find the source column feeding this output column.
            x = sx * depth / (cos * depth - sx * sin)
            x = max(-half, min(half, x))
            col_h = max(1, round(h * scale_at(x)))
            src_x = max(0, min(w - 1, round(x + half)))
            column = pygame.transform.scale(src.subsurface((src_x, 0, 1, h)), (1, col_h))
            out.blit(column, (dx, round(mid_y - col_h / 2)))
        return out
