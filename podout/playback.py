from dataclasses import dataclass
from typing import Iterable

from podout.config import PREVIOUS_RESTART_THRESHOLD, VOLUME_STEP


@dataclass
class Track:
    title: str
    artist: str = ""
    album: str = ""
    duration: float = 180.0
    artwork: str = "AlbumPlaceholder"
    rating: int = 0   # 0 = unrated; 1..5 shows that many stars


class Playback:
    """Shared playback state (queue, position, volume), read by UINowPlaying and UIStatusBar."""

    def __init__(self) -> None:
        self.queue: list[Track] = []
        self.index = 0
        self.position = 0.0
        self.playing = False
        self.volume = 0.5   # 0.0 .. 1.0
        self.shuffle = False
        self.repeat = "off"   # "off" | "all" | "one"

    @property
    def track(self) -> "Track | None":
        return self.queue[self.index] if self.queue else None

    @property
    def has_track(self) -> bool:
        return self.track is not None

    @property
    def title(self) -> str:
        return self.track.title if self.track else ""

    @property
    def artist(self) -> str:
        return self.track.artist if self.track else ""

    @property
    def album(self) -> str:
        return self.track.album if self.track else ""

    @property
    def artwork(self) -> str:
        return self.track.artwork if self.track else "AlbumPlaceholder"

    @property
    def duration(self) -> float:
        return self.track.duration if self.track else 0.0

    @property
    def rating(self) -> int:
        return self.track.rating if self.track else 0

    def set_queue(self, tracks: Iterable[Track], index: int = 0, play: bool = True) -> None:
        self.queue = list(tracks)
        self.index = max(0, min(index, len(self.queue) - 1))
        self.position = 0.0
        self.playing = play and bool(self.queue)

    def toggle(self) -> None:
        if self.has_track:
            self.playing = not self.playing

    def stop(self) -> None:
        self.playing = False
        self.position = 0.0

    def seek(self, delta: float) -> None:
        if self.has_track:
            self.position = max(0.0, min(self.duration, self.position + delta))

    def next(self) -> None:
        if self.index + 1 < len(self.queue):
            self.index += 1
            self.position = 0.0

    def previous(self) -> None:
        # Like the iPod: restart the track unless it has only just started.
        if self.position > PREVIOUS_RESTART_THRESHOLD or self.index == 0:
            self.position = 0.0
        else:
            self.index -= 1
            self.position = 0.0

    def change_volume(self, steps: int) -> None:
        self.volume = max(0.0, min(1.0, round(self.volume + steps * VOLUME_STEP, 4)))

    def update(self, dt: float) -> None:
        if not (self.playing and self.has_track):
            return
        self.position += dt
        if self.position >= self.duration:
            if self.index + 1 < len(self.queue):
                self.index += 1
                self.position = 0.0
            else:
                self.position = self.duration
                self.playing = False
