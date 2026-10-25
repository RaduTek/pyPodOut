from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from podout.ui.screen import UIScreen


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


class SlideTransition:
    """Horizontal slide between two screens. direction: +1 push (slide left), -1 pop (slide right)."""

    def __init__(self, from_screen: "UIScreen", to_screen: "UIScreen",
                 direction: int, duration: float) -> None:
        self.from_screen = from_screen
        self.to_screen = to_screen
        self.direction = direction
        self.duration = duration
        self.elapsed = 0.0

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return ease_out_cubic(min(1.0, self.elapsed / self.duration))

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def offsets(self, width: int) -> tuple[int, int]:
        """x offsets of (from_screen, to_screen)."""
        shift = round(self.progress * width) * self.direction
        return -shift, self.direction * width - shift
