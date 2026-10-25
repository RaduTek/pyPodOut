import os

import pygame

from podout.config import RES_DIR

_images = {}
_fonts = {}


def image_exists(name: str) -> bool:
    return os.path.isfile(os.path.join(RES_DIR, name + ".png"))


def load_image(name: str) -> pygame.Surface:
    """Load res/<name>.png once and cache it. Requires an initialized display."""
    img = _images.get(name)
    if img is None:
        img = pygame.image.load(os.path.join(RES_DIR, name + ".png")).convert_alpha()
        _images[name] = img
    return img


def get_font(size: int, bold: bool = True) -> pygame.font.Font:
    key = (size, bold)
    font = _fonts.get(key)
    if font is None:
        font = pygame.font.SysFont("helveticaneue,helvetica,arial", size, bold=bold)
        _fonts[key] = font
    return font
