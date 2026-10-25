import os
import sys

import pygame

from podout import keys
from podout.config import FPS, SCREEN_H, SCREEN_W
from podout.events import push_screen
from podout.playback import Playback, Track
from podout.ui import (ScreenManager, UIMenu, UIMenuItem, UILazyMenu, UIListMenuItem, UINowPlaying,
                       UIStatusBar, UIVolumeHUD, UISplashScreen)

SONGS_TOTAL = 500

DEMO_QUEUE = [
    Track("Come Together", "The Beatles", "Abbey Road", 259, rating=5),
    Track("Something", "The Beatles", "Abbey Road", 182, rating=4),
    Track("Here Comes the Sun (Original Version)", "The Beatles", "Abbey Road", 185, rating=3),
    Track("Because", "The Beatles", "Abbey Road", 165, rating=0),
]


def build_albums_menu():
    albums = [("Abbey Road", "The Beatles"), ("Kind of Blue", "Miles Davis"),
              ("Rumours", "Fleetwood Mac"), ("Discovery", "Daft Punk"),
              ("OK Computer", "Radiohead"), ("Blue", "Joni Mitchell")]
    return UIMenu("Albums", [
        UIMenuItem(f"album{i}", name, "AlbumPlaceholder88", large=True, data=artist, secondary_text=artist)
        for i, (name, artist) in enumerate(albums)
    ])


def _fmt_track_len(i):
    seconds = 120 + (i * 37) % 180   # a deterministic 2:00-4:59 pseudo-duration
    return f"{seconds // 60}:{seconds % 60:02d}"


def build_songs_menu():
    def load_songs(offset: int, limit: int) -> list[UIMenuItem]:
        return [UIMenuItem(f"song{i}", f"Track {i + 1}", secondary_text=_fmt_track_len(i))
                for i in range(offset, min(offset + limit, SONGS_TOTAL))]
    return UILazyMenu("Songs", load_songs, total_count=SONGS_TOTAL)


def build_root_menu(playback):
    def open_albums(item):
        push_screen(build_albums_menu())

    def open_songs(item):
        push_screen(build_songs_menu())

    def open_now_playing(item):
        if not playback.has_track:
            playback.set_queue(DEMO_QUEUE)
            playback.shuffle = True
            playback.repeat = "off"
        push_screen(UINowPlaying(playback))

    def toggle_item(item: UIMenuItem):
        if item.secondary_text == "On":
            item.secondary_text = "Off"
        else:
            item.secondary_text = "On"

    def open_settings(item):
        push_screen(UIMenu("Settings", [
            UIMenuItem("setting1", "Shuffle", secondary_text="On", on_select=toggle_item),
            UIMenuItem("setting2", "Repeat", secondary_text="Off", on_select=toggle_item),
            UIListMenuItem("setting3", "Equalizer", options=[("flat", "Flat"), ("bass_boost", "Bass Boost"), ("treble_boost", "Treble Boost")]),
        ]))

    def open_playlists(item):
        push_screen(UIMenu("Playlists", [
            UIMenuItem("playlist1", "My Favorites Playlist Name intended to overflow", "Playlists55"),
            UIMenuItem("playlist2", "Chill Vibes", "Playlists55"),
            UIMenuItem("playlist3", "Workout Mix", "Playlists55"),
        ]))

    return UIMenu("iPod", [
        UIMenuItem("playlists", "Playlists", "Playlists55", chevron=True, on_select=open_playlists),
        UIMenuItem("artists", "Artists", "Artists55", chevron=True),
        UIMenuItem("albums", "Albums", "Albums55", chevron=True, on_select=open_albums),
        UIMenuItem("songs", "Songs", "Songs55", chevron=True, on_select=open_songs),
        UIMenuItem("podcasts", "Podcasts", "Podcasts55", chevron=True),
        UIMenuItem("genres", "Genres", "Genres55", chevron=True),
        UIMenuItem("composers", "Composers", "Composers55", chevron=True),
        UIMenuItem("audiobooks", "Audiobooks", "Audiobooks55", chevron=True),
        UIMenuItem("genius", "Genius", "Genius55", chevron=True),
        UIMenuItem("nowplaying", "Now Playing", "NowPlaying55",  chevron=True, on_select=open_now_playing),
        UIMenuItem("settings", "Settings", chevron=True, on_select=open_settings)
    ])


def handle_media_key(event, playback):
    """Global playback keys; works on every screen, even mid-transition."""
    if event.type != pygame.KEYDOWN:
        return False
    if event.key in keys.PLAY_PAUSE:
        playback.toggle()
    elif event.key in keys.NEXT:
        playback.next()
    elif event.key in keys.PREVIOUS:
        playback.previous()
    elif event.key in keys.VOLUME_UP:
        playback.change_volume(+1)
    elif event.key in keys.VOLUME_DOWN:
        playback.change_volume(-1)
    else:
        return False
    return True


def main():
    pygame.init()
    # FULLSCREEN=1: fill the display, scaling 640x480 with the aspect ratio kept (e.g. Pi console via kmsdrm).
    fullscreen = os.environ.get("FULLSCREEN") == "1"
    flags = pygame.SCALED | pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("iPod Out")
    if fullscreen:
        pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    playback = Playback()
    manager = ScreenManager(UIStatusBar(playback), overlays=[UIVolumeHUD(playback)])
    manager.push(build_root_menu(playback), animated=False)

    manager.push(UISplashScreen(dismissible=True), animated=False)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif not handle_media_key(event, playback):
                manager.handle_event(event)
        dt = clock.get_time() / 1000.0
        playback.update(dt)
        manager.update(dt)
        manager.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
