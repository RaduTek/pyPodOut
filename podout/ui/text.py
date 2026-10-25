"""Shared helpers for drawing single-line text that may overflow its width:
ellipsis truncation and a marquee that scrolls the text back and forth.

Rendering is injected as a `render(text) -> Surface` callback so callers keep
their own font, color and caching (e.g. a per-item surface cache).
"""

from typing import Callable

import pygame

from podout.config import MARQUEE_HOLD, MARQUEE_SPEED

ELLIPSIS = "…"

RenderFn = Callable[[str], pygame.Surface]


def fit_text(render: RenderFn, text: str, max_w: int) -> pygame.Surface:
    """Render `text`, truncated with a trailing ellipsis when it exceeds max_w."""
    full = render(text)
    if not text or full.get_width() <= max_w:
        return full
    # Largest prefix length whose text + ellipsis still fits.
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if render(text[:mid].rstrip() + ELLIPSIS).get_width() <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return render(text[:lo].rstrip() + ELLIPSIS if lo else ELLIPSIS)


class Marquee:
    """Maps elapsed time to a horizontal scroll offset in [0, overflow]:
    hold at the start, scroll to reveal the end, hold, then scroll back."""

    def __init__(self) -> None:
        self.elapsed = 0.0

    def reset(self) -> None:
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def offset(self, overflow: int) -> int:
        if overflow <= 0:
            return 0
        scroll_time = overflow / MARQUEE_SPEED
        t = self.elapsed % (2 * (MARQUEE_HOLD + scroll_time))
        if t < MARQUEE_HOLD:                            # held at the start
            return 0
        t -= MARQUEE_HOLD
        if t < scroll_time:                             # scrolling to reveal the end
            return round(overflow * t / scroll_time)
        t -= scroll_time
        if t < MARQUEE_HOLD:                            # held at the end
            return overflow
        t -= MARQUEE_HOLD
        return round(overflow * (1 - t / scroll_time))  # scrolling back


def draw_text(surface: pygame.Surface, render: RenderFn, text: str, x: int, center_y: int,
              max_w: int, marquee: "Marquee | None" = None) -> None:
    """Draw `text` left-aligned at (x, center_y), vertically centered on that y.

    When it overflows max_w: scroll by `marquee`'s current offset if one is
    given, otherwise ellipsize. A line that fits is drawn as-is.
    """
    full = render(text)
    overflow = full.get_width() - max_w
    if overflow > 0 and marquee is not None:
        area = pygame.Rect(marquee.offset(overflow), 0, max_w, full.get_height())
        surface.blit(full, (x, center_y - full.get_height() // 2), area)
    elif overflow > 0:
        surf = fit_text(render, text, max_w)
        surface.blit(surf, (x, center_y - surf.get_height() // 2))
    else:
        surface.blit(full, (x, center_y - full.get_height() // 2))
