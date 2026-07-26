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
from typing import Dict, List, Tuple, Type
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
    # Стабильный ключ для каталога/сохранений (не меняется при рефакторинге
    # display-имени). Category используется для бонуса ближнего боя и как
    # задел под будущие теги/схемы оружия (модули, аффиксы).
    weapon_id: str = ""
    category: str = "melee"  # "melee" | "ranged"

    # Параметры зоны поражения (одна клетка-rect)
    reach: int = 0          # зазор от игрока, px (0 = впритык)
    rect_width: int = 32    # ширина одной клетки атаки
    rect_height: int = 32   # высота одной клетки атаки

    # Боевые параметры
    damage: int = 10
    duration_ms: int = 300  # сколько кадров показывается зона атаки
    cooldown_ms: int = 100  # минимальный интервал между атаками

    # Баллистика (только для оружия с fires_projectile=True - см. RangedWeapon).
    # У melee/AoE оружия остаются дефолты и не используются.
    fires_projectile: bool = False
    ammo_type: str = None  # None = не расходует патроны (melee, AoE)
    magazine_size: int = 0

    @abstractmethod
    def get_attack_rects(self, player_rect: pygame.Rect,
                         facing_direction: str) -> List[pygame.Rect]:
        """Вернуть список зон поражения этой атаки."""
        raise NotImplementedError


class MeleeWeapon(Weapon):
    """Меч: ближний бой, зона атаки впритык к игроку (reach=0)."""
    name = "Sword"
    weapon_id = "sword"
    category = "melee"
    color = (255, 255, 0)        # жёлтая
    reach = 0
    rect_width = 32
    rect_height = 32
    # Урон в "очках попадания" - HP врагов тоже в этих очках.
    # Меч = 1 удар = 1 HP. Heavy с 3 HP умирает за 3 удара мечом.
    damage = 1
    duration_ms = 250
    cooldown_ms = 120

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


class PolearmWeapon(Weapon):
    """Копьё/яри: средний бой, отступ в полклетки от игрока."""
    name = "Spear"
    weapon_id = "spear"
    category = "melee"
    color = (180, 220, 255)      # светло-голубая
    reach = 16
    rect_width = 32
    rect_height = 32
    damage = 1                   # как меч
    duration_ms = 280
    cooldown_ms = 180

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


class RangedWeapon(Weapon):
    """Стрелковое оружие: реальная баллистика - на try_attack() спавнится
    Projectile (см. src/entities/projectile.py), который сам летит и
    проверяет столкновения по кадрам в ProjectileManager. get_attack_rects()
    здесь не используется для урона (см. ниже) - урон наносит снаряд.
    """
    name = "Rifle"
    weapon_id = "rifle"
    category = "ranged"
    color = (255, 160, 60)       # оранжевая
    reach = 0
    rect_width = 32
    rect_height = 32
    damage = 1
    duration_ms = 200
    cooldown_ms = 250

    fires_projectile = True
    ammo_type = "bullets"
    magazine_size = 12
    projectile_speed = 480       # px/сек
    projectile_max_range = 420   # px (~13 клеток)

    def get_attack_rects(self, player_rect, facing_direction):
        # Урон наносит Projectile, не мгновенный rect - иначе Player.draw()
        # рисовал бы поверх летящей пули ещё и старую статичную рамку.
        return []


class AoeWeapon(Weapon):
    """Снаряд с областным поражением: бабах на 2 клетки впереди радиусом 3x3.

    Урон = 3 - убивает Heavy с одного попадания, Light/Fast - тем более.
    """
    name = "Bomb"
    weapon_id = "bomb"
    category = "ranged"
    color = (255, 80, 80)        # красная
    reach = 48  # 1.5 клетки до центра взрыва
    rect_width = 96   # 3 клетки
    rect_height = 96
    damage = 3                   # достаточно чтобы убить Heavy за один взрыв
    duration_ms = 400
    cooldown_ms = 600

    def get_attack_rects(self, player_rect, facing_direction):
        return [_rect_in_direction(player_rect, facing_direction,
                                   self.reach, self.rect_width, self.rect_height)]


# Каталог всех доступных типов оружия по стабильному weapon_id.
# Порядок словаря = порядок циклической смены оружия в слоте (см.
# PlayerCombat.cycle_slot_weapon). Единственный источник правды и для
# создания оружия по id (сохранения), и для стартовой раскладки.
WEAPON_CATALOG: Dict[str, Type[Weapon]] = {
    "sword": MeleeWeapon,
    "spear": PolearmWeapon,
    "rifle": RangedWeapon,
    "bomb": AoeWeapon,
}


def create_weapon(weapon_id: str) -> Weapon:
    """Создать экземпляр оружия по стабильному id из WEAPON_CATALOG."""
    return WEAPON_CATALOG[weapon_id]()


def starting_slot_assignment() -> List[str]:
    """Стартовая раскладка слотов нового игрока: 2 слота, оба - мечи
    (ближний бой)."""
    return ["sword", "spear"]

