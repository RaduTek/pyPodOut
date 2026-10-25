import sys

import pygame

from podout.config import FPS, SCREEN_H, SCREEN_W
from podout.events import push_screen
from podout.playback import Playback
from podout.ui import ScreenManager, UIMenu, UIMenuItem, UINowPlaying, UIStatusBar


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
            playback.load("Here Comes the Sun", "The Beatles", "Abbey Road", duration=185)
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


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("iPod Out")
    clock = pygame.time.Clock()

    playback = Playback()
    manager = ScreenManager(UIStatusBar(playback))
    manager.push(build_root_menu(playback))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
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
