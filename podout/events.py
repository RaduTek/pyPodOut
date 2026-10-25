import pygame

# event.menu, event.item
MENU_ITEM_SELECTED = pygame.event.custom_type()
# event.screen
PUSH_SCREEN = pygame.event.custom_type()
POP_SCREEN = pygame.event.custom_type()


def push_screen(screen):
    pygame.event.post(pygame.event.Event(PUSH_SCREEN, screen=screen))


def pop_screen():
    pygame.event.post(pygame.event.Event(POP_SCREEN))
