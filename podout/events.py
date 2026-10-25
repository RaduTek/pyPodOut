import pygame

# event.menu, event.item
MENU_ITEM_SELECTED = pygame.event.custom_type()
# event.screen, event.animated
PUSH_SCREEN = pygame.event.custom_type()
POP_SCREEN = pygame.event.custom_type()


def push_screen(screen, animated=True):
    pygame.event.post(pygame.event.Event(PUSH_SCREEN, screen=screen, animated=animated))


def pop_screen(animated=True):
    pygame.event.post(pygame.event.Event(POP_SCREEN, animated=animated))
