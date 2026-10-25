import pygame

from podout import events, keys
from podout.config import (MARGIN_X, MENU_FONT_SIZE, SCREEN_H, SCREEN_W, SCROLL_HINT_INSET,
                           SCROLL_HINT_MIN_THUMB, SCROLL_HINT_THUMB_COLOR, SCROLL_HINT_TRACK_COLOR,
                           SCROLL_HINT_WIDTH, TEXT_COLOR, TEXT_GAP, TEXT_HIGHLIGHT_COLOR,
                           TEXT_SECONDARY_COLOR, TOP_OFFSET)
from podout.resources import get_font, image_exists, load_image
from podout.ui.screen import UIScreen

SECONDARY_GAP = 8   # vertical gap between the primary and secondary line on large items


class UIMenuItem:
    def __init__(self, id, text, icon=None, highlight_icon=None, large=False,
                 chevron=False, on_select=None, data=None, secondary_text=""):
        self.id = id
        self.icon = icon                  # e.g. "Albums55"
        self.large = large                # tall (88px) row vs. standard (55px)
        self.height = 88 if large else 55
        self.chevron = chevron
        self.on_select = on_select
        self.data = data
        self.menu = None                  # set by the owning UIMenu
        self._text = text
        # Shown right-aligned before the chevron, or below the text on large items.
        self._secondary_text = secondary_text
        self._cache = {}                  # (text, color, bold) -> rendered surface
        # Default the highlight artwork to "Highlight" + icon when that file exists.
        if highlight_icon is None and icon and image_exists("Highlight" + icon):
            highlight_icon = "Highlight" + icon
        self.highlight_icon = highlight_icon

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value != self._text:
            self._text = value
            self._invalidate()

    @property
    def secondary_text(self):
        return self._secondary_text

    @secondary_text.setter
    def secondary_text(self, value):
        if value != self._secondary_text:
            self._secondary_text = value
            self._invalidate()

    def _invalidate(self):
        self._cache.clear()
        if self.menu is not None:
            self.menu.mark_dirty()

    def render(self, text, color, bold=True):
        """Return the cached render of text in color, rendering it on first use."""
        key = (text, color, bold)
        surf = self._cache.get(key)
        if surf is None:
            surf = get_font(MENU_FONT_SIZE, bold=bold).render(text, True, color)
            self._cache[key] = surf
        return surf


class UIMenu(UIScreen):
    def __init__(self, title, items):
        super().__init__(title)
        self.items = list(items)
        for item in self.items:
            item.menu = self
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
        if event.key in keys.UP:
            self.select(self.selected_index - 1)
        elif event.key in keys.DOWN:
            self.select(self.selected_index + 1)
        elif event.key in keys.SELECT:
            self.activate()
        elif event.key in keys.BACK:
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
            bg = load_image("HighlightBackground88" if item.large else "HighlightBackground55")
            bg_x = (SCREEN_W - bg.get_width()) // 2
            surface.blit(bg, (bg_x, center_y - bg.get_height() // 2))

        text_x = MARGIN_X + TEXT_GAP
        icon_name = item.highlight_icon if selected and item.highlight_icon else item.icon
        if icon_name:
            icon = load_image(icon_name)
            # Tall rows use full-width highlights, so their artwork sits flush left.
            icon_x = 0 if item.large else MARGIN_X
            surface.blit(icon, (icon_x, center_y - icon.get_height() // 2))
            text_x = icon_x + icon.get_width() + TEXT_GAP

        text_right = SCREEN_W - MARGIN_X - TEXT_GAP
        if item.chevron:
            chevron = self._highlight_chevron() if selected else load_image("Chevron")
            chevron_x = SCREEN_W - MARGIN_X - chevron.get_width() - TEXT_GAP
            surface.blit(chevron, (chevron_x, center_y - chevron.get_height() // 2))
            text_right = chevron_x - TEXT_GAP

        color = TEXT_HIGHLIGHT_COLOR if selected else TEXT_COLOR
        label = item.render(item.text, color)
        # Secondary text is never bold.
        sec_color = TEXT_HIGHLIGHT_COLOR if selected else TEXT_SECONDARY_COLOR
        sec_bold = False if item.large else True
        sec = item.render(item.secondary_text, sec_color, bold=sec_bold) if item.secondary_text else None

        if sec is not None and item.large:
            # Stack the secondary line beneath the primary one.
            block_h = label.get_height() + SECONDARY_GAP + sec.get_height()
            top = center_y - block_h // 2
            max_w = max(0, text_right - text_x)
            for surf, sy in ((label, top), (sec, top + label.get_height() + SECONDARY_GAP)):
                area = pygame.Rect(0, 0, min(surf.get_width(), max_w), surf.get_height())
                surface.blit(surf, (text_x, sy), area)
        else:
            if sec is not None:
                # Standard rows: right-align the secondary text before the chevron.
                sec_x = text_right - sec.get_width()
                surface.blit(sec, (sec_x, center_y - sec.get_height() // 2))
                text_right = sec_x - TEXT_GAP
            area = pygame.Rect(0, 0, min(label.get_width(), max(0, text_right - text_x)), label.get_height())
            surface.blit(label, (text_x, center_y - label.get_height() // 2), area)
