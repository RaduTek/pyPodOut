from podout import events
from podout.config import BG_COLOR


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

    @property
    def top(self):
        return self.stack[-1] if self.stack else None

    @property
    def depth(self):
        return len(self.stack)

    def push(self, screen):
        if self.top:
            self.top.on_exit()
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()

    def pop(self):
        if len(self.stack) <= 1:
            return None
        screen = self.stack.pop()
        screen.on_exit()
        screen.manager = None
        self.top.on_enter()
        return screen

    def replace(self, screen):
        if self.stack:
            old = self.stack.pop()
            old.on_exit()
            old.manager = None
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()

    def handle_event(self, event):
        if event.type == events.PUSH_SCREEN:
            self.push(event.screen)
            return True
        if event.type == events.POP_SCREEN:
            self.pop()
            return True
        return self.top.handle_event(event) if self.top else False

    def update(self, dt):
        if self.top:
            self.top.update(dt)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        if self.top:
            self.top.draw(surface)
        if self.status_bar:
            self.status_bar.draw(surface, self.top.title if self.top else "")
