import pygame

from podout import events
from podout.config import BG_COLOR, TRANSITION_DURATION
from podout.ui.transition import SlideTransition


class UIScreen:
    def __init__(self, title=""):
        self.title = title
        self.manager = None

    def on_enter(self):
        """Called when this screen becomes the top of the stack."""

    def on_exit(self):
        """Called when this screen is popped or covered by another screen."""

    def handle_event(self, event):
        """Return True if the event was consumed."""
        return False

    def update(self, dt):
        """Advance per-frame state; dt is in seconds."""

    def draw(self, surface):
        """Render onto surface (already cleared to the background color)."""


class ScreenManager:
    def __init__(self, status_bar=None):
        self.stack = []
        self.status_bar = status_bar
        self.transition = None
        self._buffers = None

    @property
    def top(self):
        return self.stack[-1] if self.stack else None

    @property
    def depth(self):
        return len(self.stack)

    def _start_transition(self, from_screen, to_screen, direction, animated):
        # A new navigation snaps any running transition to its end.
        self.transition = None
        if animated and from_screen is not None and from_screen is not to_screen:
            self.transition = SlideTransition(from_screen, to_screen, direction, TRANSITION_DURATION)

    def push(self, screen, animated=True):
        old = self.top
        if old:
            old.on_exit()
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()
        self._start_transition(old, screen, +1, animated)

    def pop(self, animated=True):
        if len(self.stack) <= 1:
            return None
        screen = self.stack.pop()
        screen.on_exit()
        screen.manager = None
        self.top.on_enter()
        self._start_transition(screen, self.top, -1, animated)
        return screen

    def replace(self, screen):
        self.transition = None
        if self.stack:
            old = self.stack.pop()
            old.on_exit()
            old.manager = None
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()

    def handle_event(self, event):
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

    def update(self, dt):
        if self.transition:
            self.transition.update(dt)
            if self.transition.done:
                self.transition = None
        if self.top:
            self.top.update(dt)

    def _get_buffers(self, size):
        if self._buffers is None or self._buffers[0].get_size() != size:
            self._buffers = (pygame.Surface(size).convert(), pygame.Surface(size).convert())
        return self._buffers

    def draw(self, surface):
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
