"""
InventoryScreen — экран инвентаря (v0.4.x). Пока показывает только слоты
оружия (брони/предметов ещё нет - Armor/Inventory-контейнер из BACKLOG.md
v0.4.1/v0.4.3 не реализованы) с мышиным drag-and-drop для перестановки.

Открывается из PLAYING по клавише I, ставит игру на паузу (через
GameState.INVENTORY - Game.update() уже не тикает вне PLAYING, отдельный
флаг паузы не нужен). Esc закрывает, игра возобновляется.

Конвенция как у SaveLoadMenu/HUD: не хранит player, принимает параметром;
handle_input(event, player) возвращает action dict или None - мутацию
(player.move_weapon) выполняет Game, не сам экран.

API ↔ Game:
    handle_input(event, player) → action dict | None
        {"type": "close"}                                  — Esc
        {"type": "move_weapon", "from_index": i, "to_index": j}  — drag-and-drop своп
"""
from typing import List, Optional

import pygame

from src.core.config_loader import get_config, get_color


class InventoryScreen:
    """Экран инвентаря: слоты оружия + drag-and-drop мышью."""

    SLOT_SIZE = 64
    GAP = 16
    SLOTS_Y = 300

    def __init__(self):
        self._font_title = pygame.font.Font(None, 40)
        self._font_name = pygame.font.Font(None, 26)
        self._font_digit = pygame.font.Font(None, 24)
        self._font_help = pygame.font.Font(None, 22)
        # Индекс слота, из которого сейчас тащат оружие (или None) —
        # чисто UI-состояние, не игровое (не сериализуется).
        self._dragging_index: Optional[int] = None

    # --- Геометрия -----------------------------------------------------------

    def _slot_rects(self, player) -> List[pygame.Rect]:
        """Rect'ы слотов, центрированные по горизонтали. Единая точка правды
        и для отрисовки, и для хит-тестов (в отличие от HUD, где rect'ы
        одноразовые и нигде не переиспользуются)."""
        n = len(player.weapons)
        width = get_config('WIDTH')
        total_w = n * self.SLOT_SIZE + (n - 1) * self.GAP
        start_x = (width - total_w) // 2
        return [
            pygame.Rect(
                start_x + i * (self.SLOT_SIZE + self.GAP),
                self.SLOTS_Y,
                self.SLOT_SIZE,
                self.SLOT_SIZE,
            )
            for i in range(n)
        ]

    def _slot_at(self, player, pos) -> Optional[int]:
        """Индекс слота под точкой pos, или None."""
        for i, rect in enumerate(self._slot_rects(player)):
            if rect.collidepoint(pos):
                return i
        return None

    # --- Ввод ------------------------------------------------------------

    def handle_input(self, event, player) -> Optional[dict]:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._dragging_index = None
            return {"type": "close"}

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._dragging_index = self._slot_at(player, event.pos)
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging_index is None:
                return None
            from_index = self._dragging_index
            self._dragging_index = None
            to_index = self._slot_at(player, event.pos)
            if to_index is None or to_index == from_index:
                return None
            return {"type": "move_weapon", "from_index": from_index, "to_index": to_index}

        return None

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen: pygame.Surface, player) -> None:
        screen.fill(get_color('BLACK'))
        width = get_config('WIDTH')

        title = self._font_title.render("ИНВЕНТАРЬ", True, get_color('WHITE'))
        screen.blit(title, title.get_rect(center=(width // 2, 100)))

        rects = self._slot_rects(player)
        for i, (rect, weapon) in enumerate(zip(rects, player.weapons)):
            pygame.draw.rect(screen, get_color('DARK_GRAY'), rect)
            inner = rect.inflate(-14, -14)
            pygame.draw.rect(screen, weapon.color, inner)

            is_active = (i == player.current_weapon_index)
            border_color = get_color('WHITE') if is_active else (60, 60, 60)
            border_w = 3 if is_active else 1
            pygame.draw.rect(screen, border_color, rect, border_w)

            digit_surf = self._font_digit.render(str(i + 1), True, get_color('WHITE'))
            screen.blit(digit_surf, (rect.x + 4, rect.y + 2))

            name_surf = self._font_name.render(weapon.name, True, get_color('WHITE'))
            screen.blit(name_surf, name_surf.get_rect(
                center=(rect.centerx, rect.bottom + 18)
            ))

        help_text = self._font_help.render(
            "ЛКМ — перетащить оружие между слотами  |  Esc — закрыть",
            True, (180, 180, 180),
        )
        screen.blit(help_text, help_text.get_rect(
            center=(width // 2, self.SLOTS_Y + self.SLOT_SIZE + 60)
        ))

        # Перетаскиваемая иконка следует за курсором
        if self._dragging_index is not None and 0 <= self._dragging_index < len(player.weapons):
            weapon = player.weapons[self._dragging_index]
            mx, my = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(0, 0, self.SLOT_SIZE, self.SLOT_SIZE)
            drag_rect.center = (mx, my)
            pygame.draw.rect(screen, weapon.color, drag_rect)
            pygame.draw.rect(screen, get_color('WHITE'), drag_rect, 2)
