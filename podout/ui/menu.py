from typing import Any, Callable, Iterable

import pygame

from podout import events, keys
from podout.config import (MARGIN_X, MENU_FONT_SIZE, SCREEN_H, SCREEN_W, SCROLL_HINT_INSET,
                           SCROLL_HINT_MIN_THUMB, SCROLL_HINT_THUMB_COLOR, SCROLL_HINT_TRACK_COLOR,
                           SCROLL_HINT_WIDTH, TEXT_COLOR, TEXT_GAP, TEXT_HIGHLIGHT_COLOR,
                           TEXT_SECONDARY_COLOR, TOP_OFFSET)
from podout.resources import get_font, image_exists, load_image
from podout.ui.screen import UIScreen
from podout.ui.text import Marquee, draw_text, fit_text

SECONDARY_GAP = 8   # vertical gap between the primary and secondary line on large items


class UIMenuItem:
    def __init__(self, id: str, text: str, icon: str | None = None,
                 highlight_icon: str | None = None, large: bool = False,
                 chevron: bool = False,
                 on_select: Callable[["UIMenuItem"], Any] | None = None,
                 data: Any = None, secondary_text: str = ""):
        self.id = id
        self.icon = icon                  # e.g. "Albums55"
        self.large = large                # tall (88px) row vs. standard (55px)
        self.height = 88 if large else 55
        self.chevron = chevron
        self.on_select = on_select
        self.data = data
        self.menu: "UIMenu | None" = None   # set by the owning UIMenu
        self._text = text
        # Shown right-aligned before the chevron, or below the text on large items.
        self._secondary_text = secondary_text
        self._cache: dict[tuple, pygame.Surface] = {}   # (text, color, bold) -> rendered surface
        # Default the highlight artwork to "Highlight" + icon when that file exists.
        if highlight_icon is None and icon and image_exists("Highlight" + icon):
            highlight_icon = "Highlight" + icon
        self.highlight_icon = highlight_icon

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self._invalidate()

    @property
    def secondary_text(self) -> str:
        return self._secondary_text

    @secondary_text.setter
    def secondary_text(self, value: str) -> None:
        if value != self._secondary_text:
            self._secondary_text = value
            self._invalidate()

    def _invalidate(self) -> None:
        self._cache.clear()
        if self.menu is not None:
            self.menu.mark_dirty()

    def render(self, text: str, color: tuple[int, int, int], bold: bool = True) -> pygame.Surface:
        """Return the cached render of text in color, rendering it on first use."""
        key = (text, color, bold)
        surf = self._cache.get(key)
        if surf is None:
            surf = get_font(MENU_FONT_SIZE, bold=bold).render(text, True, color)
            self._cache[key] = surf
        return surf


class UIMenu(UIScreen):
    def __init__(self, title: str, items: Iterable[UIMenuItem]) -> None:
        super().__init__(title)
        self.items = list(items)
        for item in self.items:
            item.menu = self
        self.selected_index = 0
        self.scroll_y = 0
        self.viewport = pygame.Rect(0, TOP_OFFSET, SCREEN_W, SCREEN_H - TOP_OFFSET)
        self._chevron_hl = None
        self._marquee = Marquee()   # drives the selected row's primary-text scroll

    @property
    def selected_item(self) -> "UIMenuItem | None":
        return self.items[self.selected_index] if self.items else None

    def _item_top(self, index: int) -> int:
        return sum(item.height for item in self.items[:index])

    def _content_height(self) -> int:
        return sum(item.height for item in self.items)

    @property
    def overflowing(self) -> bool:
        return self._content_height() > self.viewport.height

    def select(self, index: int) -> None:
        if not self.items:
            return
        new_index = max(0, min(index, len(self.items) - 1))
        if new_index != self.selected_index:
            self._marquee.reset()   # restart the scroll on the newly selected row
        self.selected_index = new_index
        self._scroll_to_selected()

    def update(self, dt: float) -> None:
        self._marquee.update(dt)

    def _scroll_to_selected(self) -> None:
        top = self._item_top(self.selected_index)
        bottom = top + self.items[self.selected_index].height
        if top < self.scroll_y:
            self.scroll_y = top
        elif bottom > self.scroll_y + self.viewport.height:
            self.scroll_y = bottom - self.viewport.height
        max_scroll = max(0, self._content_height() - self.viewport.height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def activate(self) -> None:
        item = self.selected_item
        if item is None:
            return
        if item.on_select:
            item.on_select(item)
        pygame.event.post(pygame.event.Event(events.MENU_ITEM_SELECTED, menu=self, item=item))

    def handle_event(self, event: pygame.event.Event) -> bool:
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

    def _highlight_chevron(self) -> pygame.Surface:
        if self._chevron_hl is None:
            chevron = load_image("Chevron").copy()
            # Keep alpha, push RGB to white.
            chevron.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            self._chevron_hl = chevron
        return self._chevron_hl

    def draw(self, surface: pygame.Surface) -> None:
        surface.set_clip(self.viewport)
        y = self.viewport.top - self.scroll_y
        for index, item in enumerate(self.items):
            if y + item.height > self.viewport.top and y < self.viewport.bottom:
                self._draw_item(surface, item, y, index == self.selected_index)
            y += item.height
        if self.overflowing:
            self._draw_scroll_hint(surface)
        surface.set_clip(None)

    def _draw_scroll_hint(self, surface: pygame.Surface) -> None:
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

    def _draw_item(self, surface: pygame.Surface, item: UIMenuItem, y: int, selected: bool) -> None:
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
        sec_color = TEXT_HIGHLIGHT_COLOR if selected else TEXT_SECONDARY_COLOR
        sec_bold = False if item.large else True   # secondary text is never bold on tall rows
        avail = max(0, text_right - text_x)
        render_primary = lambda t: item.render(t, color)
        render_secondary = lambda t: item.render(t, sec_color, sec_bold)
        # The primary line scrolls while selected and overflowing, else ellipsizes.
        marquee = self._marquee if selected else None
        primary_h = item.render(item.text, color).get_height()

        if item.large:
            # Stack the secondary line beneath the primary one; each line may use
            # the full width. Secondary is always ellipsized.
            sec = fit_text(render_secondary, item.secondary_text, avail) if item.secondary_text else None
            block_h = primary_h + (SECONDARY_GAP + sec.get_height() if sec is not None else 0)
            top = center_y - block_h // 2
            draw_text(surface, render_primary, item.text, text_x, top + primary_h // 2, avail, marquee)
            if sec is not None:
                surface.blit(sec, (text_x, top + primary_h + SECONDARY_GAP))
            return

        # Standard rows: the secondary line sits right-aligned before the chevron
        # and the primary left-aligned. The secondary is capped at half the width
        # so it can't crowd out the primary; the primary then uses whatever space
        # is left, so a short secondary leaves it room to stretch.
        primary_max = avail
        if item.secondary_text:
            sec = fit_text(render_secondary, item.secondary_text, avail // 2)
            surface.blit(sec, (text_right - sec.get_width(), center_y - sec.get_height() // 2))
            primary_max = max(0, avail - sec.get_width() - TEXT_GAP)
        draw_text(surface, render_primary, item.text, text_x, center_y, primary_max, marquee)


class UILazyMenu(UIMenu):
    """A UIMenu whose items are fetched in batches as the selection nears the end.

    `loader(offset, limit)` returns the items for [offset, offset + limit); items
    are only ever appended, so `offset` is always the current loaded count.
    When `total_count` is known it is passed so the scroll hint is sized against
    the full list from the start and does not jump as batches load.
    """

    def __init__(self, title: str, loader: Callable[[int, int], Iterable[UIMenuItem]],
                 total_count: int | None = None, batch_size: int = 20,
                 item_height: int | None = None, prefetch_margin: int = 5) -> None:
        super().__init__(title, [])
        self.loader = loader
        self.total_count = total_count
        self.batch_size = batch_size
        self.item_height = item_height
        self.prefetch_margin = prefetch_margin
        self._exhausted = False
        self._fill_viewport()

    def _content_height(self) -> int:
        loaded = super()._content_height()
        if self.total_count is not None and self.item_height:
            return loaded + max(0, self.total_count - len(self.items)) * self.item_height
        return loaded

    def select(self, index: int) -> None:
        super().select(index)
        self._maybe_load_more()

    def _maybe_load_more(self) -> None:
        while not self._exhausted and self.selected_index >= len(self.items) - self.prefetch_margin:
            if not self._load_next_batch():
                break

    def _fill_viewport(self) -> None:
        # Load enough to cover the viewport (plus a batch of margin) on first show.
        while not self._exhausted and super()._content_height() <= self.viewport.height:
            if not self._load_next_batch():
                break

    def _load_next_batch(self) -> bool:
        """Fetch and append the next batch; return True if any items were added."""
        offset = len(self.items)
        limit = self.batch_size
        if self.total_count is not None:
            limit = min(limit, self.total_count - offset)
        if self._exhausted or limit <= 0:
            self._exhausted = True
            return False

        batch = list(self.loader(offset, limit))
        for item in batch:
            item.menu = self
            self.items.append(item)
        if self.item_height is None and self.items:
            self.item_height = self.items[0].height

        if self.total_count is not None:
            self._exhausted = len(self.items) >= self.total_count
        elif len(batch) < limit:
            self._exhausted = True

        if batch:
            self.mark_dirty()
        return bool(batch)


class UIListMenuItem(UIMenuItem):
    """A UIMenuItem that opens a submenu of options when selected.

    `options` is a list of (key, label) pairs: the label is shown in the
    submenu and, for the chosen option, as this item's secondary text, while
    `value` holds the key of the current choice. Picking an option in the
    submenu updates `value`, pops back, and fires `on_select`.
    """

    def __init__(self, id: str, text: str, options: list[tuple[Any, str]],
                 icon: str | None = None, highlight_icon: str | None = None,
                 large: bool = False,
                 on_select: Callable[["UIListMenuItem"], Any] | None = None,
                 data: Any = None, value: Any = None) -> None:

        def on_select_self(item) -> None:
            self._open_options()

        # Opening a submenu, so always show the chevron. The base class's
        # `on_select` fires on activation (and opens the submenu), so keep the
        # caller's value-change callback separately.
        super().__init__(id, text, icon, highlight_icon, large, True, on_select_self, data)
        self._on_change = on_select
        self.options = options
        self._value: Any = None
        # Default to the first option when no (matching) value is given.
        self.value = value if self._index_of(value) is not None else (
            options[0][0] if options else None)

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, key: Any) -> None:
        self._value = key
        index = self._index_of(key)
        self.secondary_text = self.options[index][1] if index is not None else ""

    def _index_of(self, key: Any) -> int | None:
        for i, (k, _) in enumerate(self.options):
            if k == key:
                return i
        return None

    def _open_options(self) -> None:
        def make_handler(key: Any) -> Callable[[UIMenuItem], None]:
            def handler(_item: UIMenuItem) -> None:
                self.value = key
                events.pop_screen()
                if self._on_change:
                    self._on_change(self)
            return handler

        items = [UIMenuItem(f"{self.id}:{key}", label, chevron=False,
                            on_select=make_handler(key))
                 for key, label in self.options]
        menu = UIMenu(self.text, items)
        # Start the highlight on the current choice.
        current = self._index_of(self._value)
        if current is not None:
            menu.select(current)
        events.push_screen(menu)
