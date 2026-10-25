from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from podout.ui.screen import UIScreen

# event.menu, event.item
MENU_ITEM_SELECTED = pygame.event.custom_type()
# event.screen, event.animated
PUSH_SCREEN = pygame.event.custom_type()
POP_SCREEN = pygame.event.custom_type()
# event.key -- a select/media key held past the hold threshold (see podout.input)
KEY_HOLD = pygame.event.custom_type()


def push_screen(screen: "UIScreen", animated: bool = True) -> None:
    pygame.event.post(pygame.event.Event(PUSH_SCREEN, screen=screen, animated=animated))


def pop_screen(animated: bool = True) -> None:
    pygame.event.post(pygame.event.Event(POP_SCREEN, animated=animated))
