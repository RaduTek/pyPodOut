from typing import TYPE_CHECKING, Iterable

import pygame

from podout import events
from podout.config import BG_COLOR, TRANSITION_DURATION
from podout.ui.transition import SlideTransition

if TYPE_CHECKING:
    from podout.ui.status_bar import UIStatusBar


class UIScreen:
    def __init__(self, title: str = "") -> None:
        self.title = title
        self.manager: "ScreenManager | None" = None
        self._dirty = True

    def on_enter(self) -> None:
        """Called when this screen becomes the top of the stack."""

    def on_exit(self) -> None:
        """Called when this screen is popped or covered by another screen."""

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if the event was consumed."""
        return False

    def update(self, dt: float) -> None:
        """Advance per-frame state; dt is in seconds."""

    def mark_dirty(self) -> None:
        """Flag cached render state as stale; it is rebuilt on the next draw."""
        self._dirty = True

    def _rebuild(self) -> None:
        """Rebuild cached render state. Override in screens that cache renders."""

    def _ensure_built(self) -> None:
        """Call at the top of draw() before touching cached render state."""
        if self._dirty:
            self._rebuild()
            self._dirty = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render onto surface (already cleared to the background color)."""


class ScreenManager:
    def __init__(self, status_bar: "UIStatusBar | None" = None,
                 overlays: Iterable[object] = ()) -> None:
        self.stack: list[UIScreen] = []
        self.status_bar = status_bar
        self.overlays = list(overlays)   # drawn above everything, e.g. the volume HUD
        self.transition: SlideTransition | None = None
        self._buffers: tuple[pygame.Surface, pygame.Surface] | None = None

    @property
    def top(self) -> "UIScreen | None":
        return self.stack[-1] if self.stack else None

    @property
    def depth(self) -> int:
        return len(self.stack)

    def _start_transition(self, from_screen: "UIScreen | None", to_screen: UIScreen,
                          direction: int, animated: bool) -> None:
        # A new navigation snaps any running transition to its end.
        self.transition = None
        if animated and from_screen is not None and from_screen is not to_screen:
            self.transition = SlideTransition(from_screen, to_screen, direction, TRANSITION_DURATION)

    def push(self, screen: UIScreen, animated: bool = True) -> None:
        old = self.top
        if old:
            old.on_exit()
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()
        self._start_transition(old, screen, +1, animated)

    def pop(self, animated: bool = True) -> "UIScreen | None":
        if len(self.stack) <= 1:
            return None
        screen = self.stack.pop()
        screen.on_exit()
        screen.manager = None
        self.top.on_enter()
        self._start_transition(screen, self.top, -1, animated)
        return screen

    def replace(self, screen: UIScreen) -> None:
        self.transition = None
        if self.stack:
            old = self.stack.pop()
            old.on_exit()
            old.manager = None
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == events.PUSH_SCREEN:
            self.push(event.screen, getattr(event, "animated", True))
            return True
        if event.type == events.POP_SCREEN:
            self.pop(getattr(event, "animated", True))
            return True
        if self.transition:
            # Swallow input while screens are moving.
            return event.type in (pygame.KEYDOWN, pygame.KEYUP)
        return self.top.handle_event(event) if self.top else False

    def update(self, dt: float) -> None:
        if self.transition:
            self.transition.update(dt)
            if self.transition.done:
                self.transition = None
        if self.top:
            self.top.update(dt)
        for overlay in self.overlays:
            overlay.update(dt)

    def _get_buffers(self, size: tuple[int, int]) -> tuple[pygame.Surface, pygame.Surface]:
        if self._buffers is None or self._buffers[0].get_size() != size:
            self._buffers = (pygame.Surface(size).convert(), pygame.Surface(size).convert())
        return self._buffers

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG_COLOR)
        if self.transition:
            t = self.transition
            from_buf, to_buf = self._get_buffers(surface.get_size())
            from_x, to_x = t.offsets(surface.get_width())
            for screen, buf, x in ((t.from_screen, from_buf, from_x), (t.to_screen, to_buf, to_x)):
                buf.fill(BG_COLOR)
                screen.draw(buf)
                surface.blit(buf, (x, 0))
        elif self.top:
            self.top.draw(surface)
        if self.status_bar:
            self.status_bar.draw(surface, self.top.title if self.top else "")
        for overlay in self.overlays:
            overlay.draw(surface)
