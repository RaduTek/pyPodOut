class Playback:
    """Shared playback state, read by UINowPlaying and UIStatusBar."""

    def __init__(self):
        self.title = ""
        self.artist = ""
        self.album = ""
        self.artwork = "AlbumPlaceholder"
        self.duration = 0.0
        self.position = 0.0
        self.playing = False

    @property
    def has_track(self):
        return self.duration > 0

    def load(self, title, artist="", album="", duration=180.0, artwork="AlbumPlaceholder", play=True):
        self.title = title
        self.artist = artist
        self.album = album
        self.artwork = artwork
        self.duration = duration
        self.position = 0.0
        self.playing = play

    def toggle(self):
        if self.has_track:
            self.playing = not self.playing

    def update(self, dt):
        if self.playing and self.has_track:
            self.position = min(self.position + dt, self.duration)
            if self.position >= self.duration:
                self.playing = False
