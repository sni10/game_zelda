"""
Система оружия игрока (Strategy pattern).

Каждое оружие умеет одно: вернуть список Rect-зон поражения относительно
текущего положения и направления взгляда игрока. Поражение в этих зонах
будет проверяться внешней системой (player/game) - оружие НЕ занимается
коллизиями и уроном врагам напрямую.

Принципы:
- Симметрия по 8 направлениям (up/down/left/right + диагонали).
- Параметризация через reach/width/height/extra_rects.
- Новые виды оружия добавляются как подклассы Weapon - переопределяют
  только нужные параметры или метод get_attack_rects().
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import math
import pygame


# Единичные векторы по 8 направлениям. Диагонали нормализованы
# (1/sqrt(2) ≈ 0.7071), чтобы радиальные расстояния были одинаковыми
# во всех направлениях.
DIAGONAL = math.sqrt(2) / 2  # ~0.7071
DIRECTION_VECTORS = {
    'up':         (0.0, -1.0),
    'down':       (0.0, 1.0),
    'left':       (-1.0, 0.0),
    'right':      (1.0, 0.0),
    'up_left':    (-DIAGONAL, -DIAGONAL),
    'up_right':   (DIAGONAL, -DIAGONAL),
    'down_left':  (-DIAGONAL, DIAGONAL),
    'down_right': (DIAGONAL, DIAGONAL),
}


def _rect_in_direction(player_rect: pygame.Rect, direction: str,
                       reach: int, width: int, height: int) -> pygame.Rect:
    """Создать Rect зоны атаки в указанном направлении от игрока.

    reach - расстояние ОТ ребра игрока ДО ребра зоны атаки.
            reach=0 - впритык к игроку (меч в руке).
            reach=16 - полклетки зазора (копьё/яри).
            reach=64 - две клетки (стрельба).
    Симметрично для всех 8 направлений.
    """
    dx, dy = DIRECTION_VECTORS[direction]

    # Полу-размер игрока вдоль вектора направления.
    # Для перпендикулярных - это половина соотв. стороны (16 для 32x32).
    # Для диагоналей - проекция полудиагонали игрока на ось направления.
    player_extent = abs(dx) * (player_rect.width / 2) + abs(dy) * (player_rect.height / 2)

    # Полу-размер самой зоны атаки вдоль того же вектора.
    rect_extent = abs(dx) * (width / 2) + abs(dy) * (height / 2)

    # Центр зоны атаки: центр игрока + направление * (полу-игрок + reach + полу-зона).
    distance = player_extent + reach + rect_extent
    cx = player_rect.centerx + dx * distance
    cy = player_rect.centery + dy * distance

    return pygame.Rect(int(cx - width / 2), int(cy - height / 2), width, height)


class Weapon(ABC):
    """Базовый класс оружия."""

    # Метаданные для UI/логов
    name: str = "Weapon"
    color: Tuple[int, int, int] = (255, 255, 0)  # цвет зоны атаки в HUD

    # Параметры зоны поражения (одна клетка-rect)
    reach: int = 0          # зазор от игрока, px (0 = впритык)
    rect_width: int = 32    # ширина одной клетки атаки
    rect_height: int = 32   # высота одной клетки атаки

    # Боевые параметры
    damage: int = 10
    duration_ms: int = 300  # сколько кадров показывается зона атаки
    cooldown_ms: int = 100  # минимальный интервал между атаками

    @abstractmethod
    def get_attack_rects(self, player_rect: pygame.Rect,
                         facing_direction: str) -> List[pygame.Rect]:
        """Вернуть список зон поражения этой атаки."""
        raise NotImplementedError


class MeleeWeapon(Weapon):
    """Меч: ближний бой, зона атаки впритык к игроку (reach=0)."""
    name = "Sword"
    color = (255, 255, 0)        # жёлтая
    reach = 0
    rect_width = 32
    rect_height = 32
    damage = 15
    duration_ms = 250
    cooldown_ms = 120

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


class PolearmWeapon(Weapon):
    """Копьё/яри: средний бой, отступ в полклетки от игрока."""
    name = "Spear"
    color = (180, 220, 255)      # светло-голубая
    reach = 16
    rect_width = 32
    rect_height = 32
    damage = 12
    duration_ms = 280
    cooldown_ms = 180

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


class RangedWeapon(Weapon):
    """Лук/стрельба: дальний бой, удар на 2-3 клетки впереди.

    Атака представлена линией из 3 клеток подряд - имитация "трассы стрелы".
    В будущем заменится на настоящие projectile-сущности с движением,
    но семантика поражения сохранится.
    """
    name = "Bow"
    color = (255, 160, 60)       # оранжевая
    reach = 0  # не используется напрямую - своя логика трассы
    rect_width = 32
    rect_height = 32
    damage = 10
    duration_ms = 200
    cooldown_ms = 250

    trace_length = 3  # количество клеток в "трассе" стрелы

    def get_attack_rects(self, player_rect, facing_direction):
        # Возвращаем N последовательных клеток вдоль направления взгляда,
        # начиная с reach=0 (впритык) и наращивая на длину одной клетки.
        rects = []
        for i in range(self.trace_length):
            r = _rect_in_direction(
                player_rect, facing_direction,
                reach=i * self.rect_width,
                width=self.rect_width,
                height=self.rect_height,
            )
            rects.append(r)
        return rects


class AoeWeapon(Weapon):
    """Снаряд с областным поражением: бабах на 2 клетки впереди радиусом 3x3."""
    name = "Bomb"
    color = (255, 80, 80)        # красная
    reach = 48  # 1.5 клетки до центра взрыва
    rect_width = 96   # 3 клетки
    rect_height = 96
    damage = 25
    duration_ms = 400
    cooldown_ms = 600

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


def default_loadout() -> List[Weapon]:
    """Стандартный набор оружий игрока (порядок == клавиши 1..N)."""
    return [
        MeleeWeapon(),    # 1
        PolearmWeapon(),  # 2
        RangedWeapon(),   # 3
        AoeWeapon(),      # 4
    ]

