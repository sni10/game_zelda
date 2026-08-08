"""
HUD - класс отображения пользовательского интерфейса в игре.

Single Responsibility: рисовать UI поверх игрового мира (полоса HP, слоты оружий,
монеты, уровень, полоска XP).
Не знает про игровой цикл, ввод или мир — только про player и screen.
"""
import pygame

from src.core.config_loader import get_color


class HUD:
    """Head-Up Display: полоса здоровья + слоты оружий + монеты + level/XP."""

    # Геометрия верхнего левого блока (щит/HP/XP) - вынесена в константы,
    # чтобы полоски друг под другом не разъезжались при правке одной из них.
    SHIELD_BAR_HEIGHT = 8
    _GAP = 2
    HEALTH_BAR_Y = 10 + SHIELD_BAR_HEIGHT + _GAP        # 20
    _XP_BAR_Y = HEALTH_BAR_Y + 20 + _GAP                # 42
    _WEAPON_SLOTS_START_Y = _XP_BAR_Y + 5 + 8           # 55

    def __init__(self):
        # Шрифты создаются один раз — pygame.font.Font дорогой по инициализации
        self._font_pct = pygame.font.Font(None, 24)
        self._font_digit = pygame.font.Font(None, 20)
        self._font_name = pygame.font.Font(None, 22)
        self._font_coins = pygame.font.Font(None, 26)
        self._font_level = pygame.font.Font(None, 22)

    # --- Публичный API ----------------------------------------------------

    def draw(self, screen: pygame.Surface, player) -> None:
        """Отрисовать весь HUD."""
        if player is None:
            return
        self._draw_shield_bar(screen, player)
        self._draw_health_bar(screen, player)
        self._draw_xp_bar(screen, player)
        self._draw_level_badge(screen, player)
        self._draw_weapon_slots(screen, player)
        self._draw_coins(screen, player)

    # --- Внутренние методы рендера ---------------------------------------

    def _draw_shield_bar(self, screen: pygame.Surface, player) -> None:
        """Полоска щита брони (issue #63) - синяя, над полосой здоровья."""
        bar_width, bar_height = 200, self.SHIELD_BAR_HEIGHT
        bar_x, bar_y = 10, 10

        max_shield = player.max_shield
        pct = player.shield / max_shield if max_shield > 0 else 0
        fill_w = int(bar_width * pct)

        pygame.draw.rect(screen, get_color('DARK_GRAY'),
                         (bar_x, bar_y, bar_width, bar_height))
        if fill_w > 0:
            pygame.draw.rect(screen, (60, 140, 255),
                             (bar_x, bar_y, fill_w, bar_height))

    def _draw_health_bar(self, screen: pygame.Surface, player) -> None:
        """Полоска здоровья игрока - под полоской щита."""
        bar_width, bar_height = 200, 20
        bar_x, bar_y = 10, self.HEALTH_BAR_Y
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
        # Текст HP
        hp_text = f"{player.health}/{player.max_health}"
        text_surf = self._font_pct.render(hp_text, True, get_color('WHITE'))
        screen.blit(
            text_surf,
            (bar_x + bar_width + 10,
             bar_y + (bar_height - text_surf.get_height()) // 2),
        )

    def _draw_xp_bar(self, screen: pygame.Surface, player) -> None:
        """Тонкая полоска XP под полоской здоровья."""
        bar_x, bar_y = 10, self._XP_BAR_Y
        bar_width, bar_height = 200, 5

        stats = player.stats
        xp_next = stats.xp_to_next_level
        pct = stats.xp / xp_next if xp_next > 0 else 0
        fill_w = int(bar_width * min(pct, 1.0))

        pygame.draw.rect(screen, (30, 30, 60), (bar_x, bar_y, bar_width, bar_height))
        if fill_w > 0:
            pygame.draw.rect(screen, (80, 180, 255), (bar_x, bar_y, fill_w, bar_height))

    def _draw_level_badge(self, screen: pygame.Surface, player) -> None:
        """Уровень игрока слева от HP-бара."""
        text = f"Lv.{player.level}"
        surf = self._font_level.render(text, True, (200, 200, 255))
        # Справа от HP текста (с запасом)
        screen.blit(surf, (310, self.HEALTH_BAR_Y + 2))

    def _draw_weapon_slots(self, screen: pygame.Surface, player) -> None:
        """Слоты оружий с подсветкой активного — под полоской здоровья."""
        slot_size, gap = 36, 6
        start_x, start_y = 10, self._WEAPON_SLOTS_START_Y

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

        # Патроны (магазин/резерв) - только у оружия с ammo_type, справа от имени
        if getattr(active, 'ammo_type', None):
            ammo_text = f"{player.magazine_count()}/{player.reserve_count()}"
            ammo_surf = self._font_name.render(ammo_text, True, (220, 200, 140))
            screen.blit(
                ammo_surf,
                (start_x + name_surf.get_width() + 12, start_y + slot_size + 4),
            )

    def _draw_coins(self, screen: pygame.Surface, player) -> None:
        """Счётчик монет в правом верхнем углу (ниже миникарты)."""
        coins = player.coins
        text = f"$ {coins}"
        surf = self._font_coins.render(text, True, (255, 220, 50))
        x = screen.get_width() - 170
        y = 170  # Под миникартой
        screen.blit(surf, (x, y))
