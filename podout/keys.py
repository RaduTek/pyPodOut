"""Key groups shared by the keyboard and the IR remote (see deploy/remote.toml).

Linux input keys reach pygame through SDL as follows:
KEY_BACK -> K_AC_BACK, KEY_PLAYPAUSE -> AudioPlay, KEY_NEXTSONG -> AudioNext,
KEY_PREVIOUSSONG -> AudioPrev, KEY_VOLUMEUP/DOWN -> VolumeUp/Down.
"""
import pygame


def _sdl_key(scancode):
    # SDL keycodes for keys without a character are the scancode with bit 30 set.
    return 0x40000000 | scancode


# pygame has no named constants for these SDL keycodes.
K_VOLUMEUP = _sdl_key(128)
K_VOLUMEDOWN = _sdl_key(129)
K_AUDIONEXT = _sdl_key(258)
K_AUDIOPREV = _sdl_key(259)
K_AUDIOPLAY = _sdl_key(261)

UP = {pygame.K_UP}
DOWN = {pygame.K_DOWN}
SELECT = {pygame.K_RETURN, pygame.K_KP_ENTER}
BACK = {pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_AC_BACK}

# Media keys work on every screen; keyboard equivalents are for desktop use.
PLAY_PAUSE = {K_AUDIOPLAY, pygame.K_SPACE}
NEXT = {K_AUDIONEXT, pygame.K_RIGHT}
PREVIOUS = {K_AUDIOPREV, pygame.K_LEFT}
VOLUME_UP = {K_VOLUMEUP, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS}
VOLUME_DOWN = {K_VOLUMEDOWN, pygame.K_MINUS, pygame.K_KP_MINUS}
