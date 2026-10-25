import os
import sys

import pygame

from podout import keys
from podout.config import FPS, SCREEN_H, SCREEN_W
from podout.events import push_screen
from podout.playback import Playback, Track
from podout.ui import ScreenManager, UIMenu, UIMenuItem, UINowPlaying, UIStatusBar, UIVolumeHUD

DEMO_QUEUE = [
    Track("Come Together", "The Beatles", "Abbey Road", 259),
    Track("Something", "The Beatles", "Abbey Road", 182),
    Track("Here Comes the Sun", "The Beatles", "Abbey Road", 185),
    Track("Because", "The Beatles", "Abbey Road", 165),
]


def build_albums_menu():
    albums = [("Abbey Road", "The Beatles"), ("Kind of Blue", "Miles Davis"),
              ("Rumours", "Fleetwood Mac"), ("Discovery", "Daft Punk"),
              ("OK Computer", "Radiohead"), ("Blue", "Joni Mitchell")]
    return UIMenu("Albums", [
        UIMenuItem(f"album{i}", name, "AlbumPlaceholder88", height=88, data=artist)
        for i, (name, artist) in enumerate(albums)
    ])


def build_root_menu(playback):
    def open_albums(item):
        push_screen(build_albums_menu())

    def open_now_playing(item):
        if not playback.has_track:
            playback.set_queue(DEMO_QUEUE)
        push_screen(UINowPlaying(playback))

    return UIMenu("Music", [
        UIMenuItem("playlists", "Playlists", "Playlists55"),
        UIMenuItem("artists", "Artists", "Artists55"),
        UIMenuItem("albums", "Albums", "Albums55", on_select=open_albums),
        UIMenuItem("songs", "Songs", "Songs55"),
        UIMenuItem("podcasts", "Podcasts", "Podcasts55"),
        UIMenuItem("genres", "Genres", "Genres55"),
        UIMenuItem("composers", "Composers", "Composers55"),
        UIMenuItem("audiobooks", "Audiobooks", "Audiobooks55"),
        UIMenuItem("genius", "Genius", "Genius55"),
        UIMenuItem("nowplaying", "Now Playing", "NowPlaying55", on_select=open_now_playing),
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
