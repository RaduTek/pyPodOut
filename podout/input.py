"""Centralized key handling: auto-repeat and hold detection.

Raw pygame KEYDOWN/KEYUP events are fed to an `InputManager`, which turns them
into dispatched actions:

* Repeat keys (up, down, volume up/down) fire once on press, then again every
  `repeat_interval` seconds once held past `repeat_delay` -- re-dispatched as
  synthetic KEYDOWN events so existing handlers see them unchanged.
* Hold keys (select, play/pause, next, previous) fire their normal action as a
  KEYDOWN on release (a tap); if held past `hold_time` instead, they fire a
  one-shot `events.KEY_HOLD` event and the tap is suppressed.
* Any other key is dispatched immediately on press.
"""

from typing import Callable

import pygame

from podout import events, keys
from podout.config import KEY_HOLD_TIME, KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL

_REPEAT_GROUPS = (keys.UP, keys.DOWN, keys.VOLUME_UP, keys.VOLUME_DOWN)
_HOLD_GROUPS = (keys.SELECT, keys.PLAY_PAUSE, keys.NEXT, keys.PREVIOUS)


class _Held:
    __slots__ = ("key", "category", "elapsed", "next_repeat", "hold_fired")

    def __init__(self, key: int, category: str) -> None:
        self.key = key
        self.category = category
        self.elapsed = 0.0
        self.next_repeat = 0.0
        self.hold_fired = False


class InputManager:
    def __init__(self, dispatch: Callable[[pygame.event.Event], None],
                 repeat_delay: float = KEY_REPEAT_DELAY,
                 repeat_interval: float = KEY_REPEAT_INTERVAL,
                 hold_time: float = KEY_HOLD_TIME) -> None:
        self.dispatch = dispatch
        self.repeat_delay = repeat_delay
        self.repeat_interval = repeat_interval
        self.hold_time = hold_time
        self._category: dict[int, str] = {}
        for group in _REPEAT_GROUPS:
            for key in group:
                self._category[key] = "repeat"
        for group in _HOLD_GROUPS:
            for key in group:
                self._category[key] = "hold"
        self._held: dict[int, _Held] = {}

    def handle_key(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._press(event.key)
        elif event.type == pygame.KEYUP:
            self._release(event.key)

    def _press(self, key: int) -> None:
        if key in self._held:
            return   # already tracking; ignore a repeated down (OS/remote auto-repeat)
        category = self._category.get(key)
        if category is None:
            self._dispatch_key(key)   # plain key (e.g. back): act immediately
            return
        state = _Held(key, category)
        self._held[key] = state
        if category == "repeat":
            self._dispatch_key(key)                     # fire once immediately
            state.next_repeat = self.repeat_delay       # then repeat after the delay
        # hold keys do nothing until release (tap) or the hold threshold

    def _release(self, key: int) -> None:
        state = self._held.pop(key, None)
        if state is not None and state.category == "hold" and not state.hold_fired:
            self._dispatch_key(key)   # a tap: fire the normal action on release

    def update(self, dt: float) -> None:
        for state in list(self._held.values()):
            state.elapsed += dt
            if state.category == "repeat":
                while state.elapsed >= state.next_repeat:
                    self._dispatch_key(state.key)
                    state.next_repeat += self.repeat_interval
            elif not state.hold_fired and state.elapsed >= self.hold_time:
                state.hold_fired = True
                self.dispatch(pygame.event.Event(events.KEY_HOLD, key=state.key))

    def _dispatch_key(self, key: int) -> None:
        self.dispatch(pygame.event.Event(pygame.KEYDOWN, key=key))
