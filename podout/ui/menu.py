from dataclasses import dataclass
from typing import Any, Callable, Optional

import pygame

from podout import events
from podout.config import (MARGIN_X, MENU_FONT_SIZE, SCREEN_H, SCREEN_W, SCROLL_HINT_INSET,
                           SCROLL_HINT_MIN_THUMB, SCROLL_HINT_THUMB_COLOR, SCROLL_HINT_TRACK_COLOR,
                           SCROLL_HINT_WIDTH, TEXT_COLOR, TEXT_GAP, TEXT_HIGHLIGHT_COLOR,
                           TOP_OFFSET)
from podout.resources import get_font, image_exists, load_image
from podout.ui.screen import UIScreen


@dataclass
class UIMenuItem:
    id: str
    text: str
    icon: Optional[str] = None            # e.g. "Albums55"
    highlight_icon: Optional[str] = None  # defaults to "Highlight" + icon if that file exists
    height: int = 55                      # 55 or 88
    chevron: bool = True
    on_select: Optional[Callable[["UIMenuItem"], None]] = None
    data: Any = None

    def __post_init__(self):
        if self.highlight_icon is None and self.icon and image_exists("Highlight" + self.icon):
            self.highlight_icon = "Highlight" + self.icon


class UIMenu(UIScreen):
    def __init__(self, title, items):
        super().__init__(title)
        self.items = list(items)
        self.selected_index = 0
        self.scroll_y = 0
        self.viewport = pygame.Rect(0, TOP_OFFSET, SCREEN_W, SCREEN_H - TOP_OFFSET)
        self._chevron_hl = None

    @property
    def selected_item(self):
        return self.items[self.selected_index] if self.items else None

    def _item_top(self, index):
        return sum(item.height for item in self.items[:index])

    def _content_height(self):
        return sum(item.height for item in self.items)

    @property
    def overflowing(self):
        return self._content_height() > self.viewport.height

    def select(self, index):
        if not self.items:
            return
        self.selected_index = max(0, min(index, len(self.items) - 1))
        self._scroll_to_selected()

    def _scroll_to_selected(self):
        top = self._item_top(self.selected_index)
        bottom = top + self.items[self.selected_index].height
        if top < self.scroll_y:
            self.scroll_y = top
        elif bottom > self.scroll_y + self.viewport.height:
            self.scroll_y = bottom - self.viewport.height
        max_scroll = max(0, self._content_height() - self.viewport.height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def activate(self):
        item = self.selected_item
        if item is None:
            return
        if item.on_select:
            item.on_select(item)
        pygame.event.post(pygame.event.Event(events.MENU_ITEM_SELECTED, menu=self, item=item))

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_UP:
            self.select(self.selected_index - 1)
        elif event.key == pygame.K_DOWN:
            self.select(self.selected_index + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.activate()
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            if not (self.manager and self.manager.depth > 1):
                return False
            events.pop_screen()
        else:
            return False
        return True

    def _highlight_chevron(self):
        if self._chevron_hl is None:
            chevron = load_image("Chevron").copy()
            # Keep alpha, push RGB to white.
            chevron.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            self._chevron_hl = chevron
        return self._chevron_hl

    def draw(self, surface):
        surface.set_clip(self.viewport)
        y = self.viewport.top - self.scroll_y
        for index, item in enumerate(self.items):
            if y + item.height > self.viewport.top and y < self.viewport.bottom:
                self._draw_item(surface, item, y, index == self.selected_index)
            y += item.height
        if self.overflowing:
            self._draw_scroll_hint(surface)
        surface.set_clip(None)

    def _draw_scroll_hint(self, surface):
        vp = self.viewport
        content_h = self._content_height()
        track = pygame.Rect(vp.right - SCROLL_HINT_INSET - SCROLL_HINT_WIDTH, vp.top + SCROLL_HINT_INSET,
                            SCROLL_HINT_WIDTH, vp.height - 2 * SCROLL_HINT_INSET)
        thumb_h = max(SCROLL_HINT_MIN_THUMB, round(track.height * vp.height / content_h))
        max_scroll = content_h - vp.height
        thumb_y = track.top + round((track.height - thumb_h) * self.scroll_y / max_scroll)
        radius = SCROLL_HINT_WIDTH // 2
        pygame.draw.rect(surface, SCROLL_HINT_TRACK_COLOR, track, border_radius=radius)
        pygame.draw.rect(surface, SCROLL_HINT_THUMB_COLOR,
                         (track.left, thumb_y, track.width, thumb_h), border_radius=radius)

    def _draw_item(self, surface, item, y, selected):
        center_y = y + item.height // 2

        if selected:
            bg = load_image("HighlightBackground88" if item.height >= 88 else "HighlightBackground55")
            bg_x = (SCREEN_W - bg.get_width()) // 2
            surface.blit(bg, (bg_x, center_y - bg.get_height() // 2))

        text_x = MARGIN_X + TEXT_GAP
        icon_name = item.highlight_icon if selected and item.highlight_icon else item.icon
        if icon_name:
            icon = load_image(icon_name)
            # Tall rows use full-width highlights, so their artwork sits flush left.
            icon_x = 0 if item.height >= 88 else MARGIN_X
            surface.blit(icon, (icon_x, center_y - icon.get_height() // 2))
            text_x = icon_x + icon.get_width() + TEXT_GAP

        text_right = SCREEN_W - MARGIN_X - TEXT_GAP
        if item.chevron:
            chevron = self._highlight_chevron() if selected else load_image("Chevron")
            chevron_x = SCREEN_W - MARGIN_X - chevron.get_width() - TEXT_GAP
            surface.blit(chevron, (chevron_x, center_y - chevron.get_height() // 2))
            text_right = chevron_x - TEXT_GAP

        color = TEXT_HIGHLIGHT_COLOR if selected else TEXT_COLOR
        label = get_font(MENU_FONT_SIZE).render(item.text, True, color)
        area = pygame.Rect(0, 0, min(label.get_width(), max(0, text_right - text_x)), label.get_height())
        surface.blit(label, (text_x, center_y - label.get_height() // 2), area)
