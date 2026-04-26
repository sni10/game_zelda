"""
HUD - класс отображения пользовательского интерфейса в игре.

Single Responsibility: рисовать UI поверх игрового мира (полоса HP, слоты оружий).
Не знает про игровой цикл, ввод или мир — только про player и screen.
"""
import pygame

from src.core.config_loader import get_color


class HUD:
    """Head-Up Display: полоса здоровья + слоты оружий + (в будущем) другие элементы."""

    def __init__(self):
        # Шрифты создаются один раз — pygame.font.Font дорогой по инициализации
        self._font_pct = pygame.font.Font(None, 24)
        self._font_digit = pygame.font.Font(None, 20)
        self._font_name = pygame.font.Font(None, 22)

    # --- Публичный API ----------------------------------------------------

    def draw(self, screen: pygame.Surface, player) -> None:
        """Отрисовать весь HUD. player должен иметь .health, .max_health, .weapons, .current_weapon_index."""
        if player is None:
            return
        self._draw_health_bar(screen, player)
        self._draw_weapon_slots(screen, player)

    # --- Внутренние методы рендера ---------------------------------------

    def _draw_health_bar(self, screen: pygame.Surface, player) -> None:
        """Полоска здоровья игрока в верхнем-левом углу."""
        bar_width, bar_height = 200, 20
        bar_x, bar_y = 10, 10
        border_width = 2

        pct = player.health / player.max_health if player.max_health > 0 else 0
        health_w = int(bar_width * pct)

        # Фон
        pygame.draw.rect(screen, get_color('DARK_GRAY'),
                         (bar_x, bar_y, bar_width, bar_height))
        # Заливка
        if health_w > 0:
            pygame.draw.rect(screen, get_color('GREEN'),
                             (bar_x, bar_y, health_w, bar_height))
        # Рамка
        pygame.draw.rect(
            screen, get_color('WHITE'),
            (bar_x - border_width, bar_y - border_width,
             bar_width + border_width * 2, bar_height + border_width * 2),
            border_width,
        )
        # Текст в процентах
        pct_display = int(round(pct * 100))
        text_surf = self._font_pct.render(f"{pct_display}%", True, get_color('WHITE'))
        screen.blit(
            text_surf,
            (bar_x + bar_width + 10,
             bar_y + (bar_height - text_surf.get_height()) // 2),
        )

    def _draw_weapon_slots(self, screen: pygame.Surface, player) -> None:
        """Слоты оружий с подсветкой активного — под полоской здоровья."""
        slot_size, gap = 36, 6
        start_x, start_y = 10, 40

        for i, weapon in enumerate(player.weapons):
            slot_x = start_x + i * (slot_size + gap)
            slot_rect = pygame.Rect(slot_x, start_y, slot_size, slot_size)

            pygame.draw.rect(screen, get_color('DARK_GRAY'), slot_rect)
            inner = slot_rect.inflate(-8, -8)
            pygame.draw.rect(screen, weapon.color, inner)

            is_active = (i == player.current_weapon_index)
            border_color = get_color('WHITE') if is_active else (60, 60, 60)
            border_w = 3 if is_active else 1
            pygame.draw.rect(screen, border_color, slot_rect, border_w)

            digit_surf = self._font_digit.render(str(i + 1), True, get_color('WHITE'))
            screen.blit(digit_surf, (slot_x + 3, start_y + 2))

        # Имя активного оружия под слотами
        active = player.current_weapon
        name_surf = self._font_name.render(active.name, True, get_color('WHITE'))
        screen.blit(name_surf, (start_x, start_y + slot_size + 4))

