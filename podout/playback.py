from dataclasses import dataclass

from podout.config import PREVIOUS_RESTART_THRESHOLD, VOLUME_STEP


@dataclass
class Track:
    title: str
    artist: str = ""
    album: str = ""
    duration: float = 180.0
    artwork: str = "AlbumPlaceholder"


class Playback:
    """Shared playback state (queue, position, volume), read by UINowPlaying and UIStatusBar."""

    def __init__(self):
        self.queue = []
        self.index = 0
        self.position = 0.0
        self.playing = False
        self.volume = 0.5   # 0.0 .. 1.0

    @property
    def track(self):
        return self.queue[self.index] if self.queue else None

    @property
    def has_track(self):
        return self.track is not None

    @property
    def title(self):
        return self.track.title if self.track else ""

    @property
    def artist(self):
        return self.track.artist if self.track else ""

    @property
    def album(self):
        return self.track.album if self.track else ""

    @property
    def artwork(self):
        return self.track.artwork if self.track else "AlbumPlaceholder"

    @property
    def duration(self):
        return self.track.duration if self.track else 0.0

    def set_queue(self, tracks, index=0, play=True):
        self.queue = list(tracks)
        self.index = max(0, min(index, len(self.queue) - 1))
        self.position = 0.0
        self.playing = play and bool(self.queue)

    def toggle(self):
        if self.has_track:
            self.playing = not self.playing

    def next(self):
        if self.index + 1 < len(self.queue):
            self.index += 1
            self.position = 0.0

    def previous(self):
        # Like the iPod: restart the track unless it has only just started.
        if self.position > PREVIOUS_RESTART_THRESHOLD or self.index == 0:
            self.position = 0.0
        else:
            self.index -= 1
            self.position = 0.0

    def change_volume(self, steps):
        self.volume = max(0.0, min(1.0, round(self.volume + steps * VOLUME_STEP, 4)))

    def update(self, dt):
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
