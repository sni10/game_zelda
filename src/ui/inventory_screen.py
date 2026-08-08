"""
InventoryScreen — экран инвентаря (v0.4.x). Показывает слоты оружия
(мышиный drag-and-drop) и полоски состояния брони (issue #63) - броня
пока фиксированный стартовый комплект без drag-and-drop, см.
src/entities/armor.py.

Открывается из PLAYING по клавише I или Tab, ставит игру на паузу (через
GameState.INVENTORY - Game.update() уже не тикает вне PLAYING, отдельный
флаг паузы не нужен). Esc/I/Tab закрывают, игра возобновляется.

Всегда показывает все MAX_WEAPON_SLOTS (8) слотов, а не только уже
разлоченные игроком - ещё не открытые слоты рисуются вдвое прозрачнее и не
реагируют на мышь, чтобы игрок сразу видел, сколько слотов ему ещё предстоит
открыть прокачкой. Ниже - каталог всех типов оружия (WEAPON_CATALOG):
перетаскивание иконки из каталога в разлоченный слот назначает туда этот тип
оружия (замена убранному переключению по Tab). Пока доступны все виды сразу -
в будущем, когда появится дерево прокачки, часть оружия (в первую очередь
огнестрел) будет открываться по условию, и это будет видно в каталоге так же,
как сейчас видно по слотам.

Конвенция как у SaveLoadMenu/HUD: не хранит player, принимает параметром;
handle_input(event, player) возвращает action dict или None - мутацию
(player.move_weapon/set_slot_weapon) выполняет Game, не сам экран.

API ↔ Game:
    handle_input(event, player) → action dict | None
        {"type": "close"}                                            — Esc/I/Tab
        {"type": "move_weapon", "from_index": i, "to_index": j}       — своп слотов
        {"type": "set_slot_weapon", "index": i, "weapon_id": wid}     — оружие из каталога в слот
"""
from typing import List, Optional, Tuple

import pygame

from src.core.config_loader import get_config, get_color
from src.entities.armor import SLOT_NAMES
from src.entities.player_combat import MAX_WEAPON_SLOTS
from src.entities.weapons import WEAPON_CATALOG


# Подписи слотов брони на экране инвентаря (см. src/entities/armor.py).
_ARMOR_SLOT_LABELS = {
    "helmet": "Шлем",
    "chest": "Кираса",
    "arms": "Наручи",
    "legs": "Наколенники",
}


class InventoryScreen:
    """Экран инвентаря: все слоты оружия (в т.ч. locked) + каталог + DnD."""

    SLOT_SIZE = 64
    GAP = 16
    SLOTS_Y = 260
    CATALOG_Y = 440
    ARMOR_Y = 580
    LOCKED_ALPHA = 128  # вдвое меньшая непрозрачность (255 // 2) для locked-слотов

    def __init__(self):
        self._font_title = pygame.font.Font(None, 40)
        self._font_section = pygame.font.Font(None, 26)
        self._font_name = pygame.font.Font(None, 22)
        self._font_digit = pygame.font.Font(None, 24)
        self._font_help = pygame.font.Font(None, 22)
        # ("slot", index) при перетаскивании между слотами,
        # ("catalog", weapon_id) при перетаскивании оружия из каталога - или None.
        self._dragging: Optional[Tuple[str, object]] = None

    # --- Геометрия -----------------------------------------------------------

    def _slot_rects(self) -> List[pygame.Rect]:
        """Rect'ы ВСЕХ MAX_WEAPON_SLOTS слотов - фиксированный ряд, не
        зависящий от того, сколько игрок уже разлочил, чтобы открытие нового
        слота не двигало уже нарисованные (см. класс docstring)."""
        n = MAX_WEAPON_SLOTS
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

    def _catalog_rects(self) -> List[pygame.Rect]:
        """Rect'ы каталога - по одному на каждый weapon_id из WEAPON_CATALOG."""
        n = len(WEAPON_CATALOG)
        width = get_config('WIDTH')
        total_w = n * self.SLOT_SIZE + (n - 1) * self.GAP
        start_x = (width - total_w) // 2
        return [
            pygame.Rect(
                start_x + i * (self.SLOT_SIZE + self.GAP),
                self.CATALOG_Y,
                self.SLOT_SIZE,
                self.SLOT_SIZE,
            )
            for i in range(n)
        ]

    def _armor_bar_rects(self) -> List[pygame.Rect]:
        """Rect'ы полосок состояния брони - по одному на каждый слот из
        SLOT_NAMES (helmet/chest/arms/legs), в фиксированном порядке."""
        n = len(SLOT_NAMES)
        width = get_config('WIDTH')
        bar_w, bar_h, gap = 140, 20, 24
        total_w = n * bar_w + (n - 1) * gap
        start_x = (width - total_w) // 2
        return [
            pygame.Rect(start_x + i * (bar_w + gap), self.ARMOR_Y, bar_w, bar_h)
            for i in range(n)
        ]

    def _slot_at(self, player, pos) -> Optional[int]:
        """Индекс АКТИВНОГО (уже разлоченного) слота под точкой pos, или
        None - в locked-слоты (index >= len(player.weapons)) бросить/утащить
        оружие нельзя, они там только для превью."""
        for i, rect in enumerate(self._slot_rects()):
            if i >= len(player.weapons):
                break
            if rect.collidepoint(pos):
                return i
        return None

    def _catalog_weapon_at(self, pos) -> Optional[str]:
        """weapon_id под точкой pos в ряду каталога, или None."""
        for weapon_id, rect in zip(WEAPON_CATALOG, self._catalog_rects()):
            if rect.collidepoint(pos):
                return weapon_id
        return None

    # --- Ввод ------------------------------------------------------------

    def handle_input(self, event, player) -> Optional[dict]:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_i, pygame.K_TAB
        ):
            self._dragging = None
            return {"type": "close"}

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            slot_index = self._slot_at(player, event.pos)
            if slot_index is not None:
                self._dragging = ("slot", slot_index)
                return None
            weapon_id = self._catalog_weapon_at(event.pos)
            if weapon_id is not None:
                self._dragging = ("catalog", weapon_id)
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging is None:
                return None
            source_kind, source_value = self._dragging
            self._dragging = None
            to_index = self._slot_at(player, event.pos)
            if to_index is None:
                return None
            if source_kind == "slot":
                if to_index == source_value:
                    return None
                return {"type": "move_weapon", "from_index": source_value, "to_index": to_index}
            # source_kind == "catalog"
            return {"type": "set_slot_weapon", "index": to_index, "weapon_id": source_value}

        return None

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen: pygame.Surface, player) -> None:
        screen.fill(get_color('BLACK'))
        width = get_config('WIDTH')

        title = self._font_title.render("ИНВЕНТАРЬ", True, get_color('WHITE'))
        screen.blit(title, title.get_rect(center=(width // 2, 60)))

        section = self._font_section.render(
            f"Слоты оружия ({len(player.weapons)}/{MAX_WEAPON_SLOTS} открыто)",
            True, get_color('WHITE'),
        )
        screen.blit(section, section.get_rect(center=(width // 2, self.SLOTS_Y - 30)))

        for i, rect in enumerate(self._slot_rects()):
            if i < len(player.weapons):
                self._draw_active_slot(screen, rect, i, player)
            else:
                self._draw_locked_slot(screen, rect, i)

        catalog_title = self._font_section.render(
            "Всё оружие (перетащи в слот)", True, get_color('WHITE'),
        )
        screen.blit(catalog_title, catalog_title.get_rect(
            center=(width // 2, self.CATALOG_Y - 30)
        ))

        for weapon_id, rect in zip(WEAPON_CATALOG, self._catalog_rects()):
            self._draw_catalog_entry(screen, rect, weapon_id)

        self._draw_armor_section(screen, player)

        help_text = self._font_help.render(
            "ЛКМ — перетащить оружие в слот или поменять слоты местами  |  Esc/I/Tab — закрыть",
            True, (180, 180, 180),
        )
        screen.blit(help_text, help_text.get_rect(
            center=(width // 2, self.ARMOR_Y + 60)
        ))

        self._draw_dragged_icon(screen, player)

    def _draw_armor_section(self, screen: pygame.Surface, player) -> None:
        """Полоски состояния (текущий/максимальный щит) каждого надетого
        предмета брони (issue #63) - чтобы было видно, какая часть брони
        уже пробита, не только суммарный щит в HUD."""
        width = get_config('WIDTH')
        section = self._font_section.render(
            "Броня (состояние щита)", True, get_color('WHITE'),
        )
        screen.blit(section, section.get_rect(center=(width // 2, self.ARMOR_Y - 26)))

        for slot_name, rect in zip(SLOT_NAMES, self._armor_bar_rects()):
            armor = player.equipment.slots.get(slot_name)

            pygame.draw.rect(screen, (40, 40, 40), rect)
            if armor is not None and armor.max_shield > 0:
                pct = armor.current_shield / armor.max_shield
                fill_w = int(rect.width * pct)
                if fill_w > 0:
                    pygame.draw.rect(screen, (60, 140, 255),
                                     (rect.x, rect.y, fill_w, rect.height))
            pygame.draw.rect(screen, (90, 90, 90), rect, 1)

            if armor is not None:
                value_text = (f"{_ARMOR_SLOT_LABELS[slot_name]} "
                             f"{armor.current_shield}/{armor.max_shield}")
            else:
                value_text = f"{_ARMOR_SLOT_LABELS[slot_name]} —"
            value_surf = self._font_name.render(value_text, True, get_color('WHITE'))
            screen.blit(value_surf, value_surf.get_rect(center=(rect.centerx, rect.bottom + 14)))

    def _draw_active_slot(self, screen, rect, i, player) -> None:
        weapon = player.weapons[i]
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
        screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.bottom + 14)))

    def _draw_locked_slot(self, screen, rect, i) -> None:
        """Ещё не разлоченный слот - виден, но неактивен (не принимает
        drag-and-drop): вдвое меньшая непрозрачность (см. класс docstring),
        чтобы отличаться от активных слотов с первого взгляда."""
        slot_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        local_rect = slot_surf.get_rect()
        pygame.draw.rect(slot_surf, get_color('DARK_GRAY'), local_rect)
        pygame.draw.rect(slot_surf, (60, 60, 60), local_rect, 1)
        digit_surf = self._font_digit.render(str(i + 1), True, get_color('WHITE'))
        slot_surf.blit(digit_surf, (4, 2))
        slot_surf.set_alpha(self.LOCKED_ALPHA)
        screen.blit(slot_surf, rect.topleft)

    def _draw_catalog_entry(self, screen, rect, weapon_id) -> None:
        weapon_cls = WEAPON_CATALOG[weapon_id]
        pygame.draw.rect(screen, get_color('DARK_GRAY'), rect)
        inner = rect.inflate(-14, -14)
        pygame.draw.rect(screen, weapon_cls.color, inner)
        pygame.draw.rect(screen, (60, 60, 60), rect, 1)

        name_surf = self._font_name.render(weapon_cls.name, True, get_color('WHITE'))
        screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.bottom + 14)))

    def _draw_dragged_icon(self, screen, player) -> None:
        """Перетаскиваемая иконка следует за курсором - неважно, тащат её
        из слота или из каталога."""
        if self._dragging is None:
            return
        kind, value = self._dragging
        if kind == "slot":
            if not (0 <= value < len(player.weapons)):
                return
            weapon = player.weapons[value]
            color = weapon.color
        else:
            color = WEAPON_CATALOG[value].color

        mx, my = pygame.mouse.get_pos()
        drag_rect = pygame.Rect(0, 0, self.SLOT_SIZE, self.SLOT_SIZE)
        drag_rect.center = (mx, my)
        pygame.draw.rect(screen, color, drag_rect)
        pygame.draw.rect(screen, get_color('WHITE'), drag_rect, 2)
