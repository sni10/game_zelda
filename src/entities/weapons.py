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


def _rect_in_vector_direction(player_rect: pygame.Rect, dx: float, dy: float,
                              reach: int, width: int, height: int) -> pygame.Rect:
    """Создать Rect зоны атаки вдоль произвольного юнит-вектора (dx, dy) -
    не только 8 фиксированных направлений, любой угол (360° прицеливание).

    reach - расстояние ОТ ребра игрока ДО ребра зоны атаки.
            reach=0 - впритык к игроку (меч в руке).
            reach=16 - полклетки зазора (копьё/яри).
            reach=64 - две клетки (стрельба).
    """
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


def _rect_in_direction(player_rect: pygame.Rect, direction: str,
                       reach: int, width: int, height: int) -> pygame.Rect:
    """Обёртка над _rect_in_vector_direction для одного из 8 именованных
    направлений - сохранена ради существующих тестов/вызовов по строке."""
    dx, dy = DIRECTION_VECTORS[direction]
    return _rect_in_vector_direction(player_rect, dx, dy, reach, width, height)


def pellet_directions(aim_dx: float, aim_dy: float, pellet_count: int,
                      spread_angle_deg: float) -> List[Tuple[float, float]]:
    """Вернуть pellet_count юнит-векторов направлений для одного залпа.

    pellet_count<=1 - вернуть только (aim_dx, aim_dy) без веера (Rifle/SMG).
    pellet_count>1 (Shotgun) - равномерный веер в пределах spread_angle_deg
    градусов вокруг направления прицела; при нечётном pellet_count один из
    векторов всегда приходится точно на центральную ось прицела (i == середина).
    """
    if pellet_count <= 1:
        return [(aim_dx, aim_dy)]
    base_angle = math.atan2(aim_dy, aim_dx)
    spread = math.radians(spread_angle_deg)
    return [
        (math.cos(angle), math.sin(angle))
        for angle in (
            base_angle + spread * (i / (pellet_count - 1) - 0.5)
            for i in range(pellet_count)
        )
    ]


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
    # 1 нажатие = 1 патрон всегда, независимо от того, сколько снарядов
    # реально вылетает (burst_count/pellet_count) - магазин на 9 патронов
    # даёт 9 выстрелов и у дробовика (5 пуль/выстрел), и у SMG (3 пули/выстрел).

    # Очередь (burst-fire, см. BurstRifle): burst_count последовательных
    # выстрелов с интервалом burst_delay_ms внутри одного attack_id - таймингом
    # рулит Game._spawn_projectile/update() (см. game.py), не Weapon.
    burst_count: int = 1
    burst_delay_ms: int = 0

    # Дробовик (веерный разлёт, см. ShotgunWeapon): pellet_count пуль за
    # один выстрел, равномерно распределённых по spread_angle_deg градусов
    # вокруг направления прицела (см. Game._spawn_projectile).
    pellet_count: int = 1
    spread_angle_deg: float = 0.0

    @abstractmethod
    def get_attack_rects(self, player_rect: pygame.Rect,
                         aim_dx: float, aim_dy: float) -> List[pygame.Rect]:
        """Вернуть список зон поражения этой атаки. (aim_dx, aim_dy) -
        нормализованный вектор прицела (360°, не только 8 направлений)."""
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

    def get_attack_rects(self, player_rect, aim_dx, aim_dy):
        return [_rect_in_vector_direction(player_rect, aim_dx, aim_dy,
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

    def get_attack_rects(self, player_rect, aim_dx, aim_dy):
        return [_rect_in_vector_direction(player_rect, aim_dx, aim_dy,
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
    # Скорострельное оружие - дистанцию не ограничиваем: пуля летит, пока
    # не упрётся в стену/границу мира (см. ProjectileManager), не по таймеру.
    projectile_max_range = float('inf')

    def get_attack_rects(self, player_rect, aim_dx, aim_dy):
        # Урон наносит Projectile, не мгновенный rect - иначе Player.draw()
        # рисовал бы поверх летящей пули ещё и старую статичную рамку.
        return []


class BurstRifle(RangedWeapon):
    """SMG: очередь по 3 пули за одно нажатие пробела/ЛКМ, но расходует
    ровно 1 патрон из магазина (как и одиночный Rifle) - магазин на 24
    патрона даёт 24 очереди (72 пули), не 8.

    Выстрелы разнесены во времени (burst_delay_ms), не мгновенны все разом -
    таймингом рулит Game.update() (см. _burst_shots_fired в game.py).
    """
    name = "SMG"
    weapon_id = "smg"
    color = (255, 205, 60)       # золотисто-жёлтая (отличима от Rifle)
    reach = 0
    damage = 1
    duration_ms = 260            # покрывает все 3 выстрела очереди с запасом
    cooldown_ms = 380            # общий откат после всей очереди

    fires_projectile = True
    ammo_type = "bullets"
    magazine_size = 24
    projectile_speed = 520
    # Скорострельное оружие - без ограничения дистанции (см. RangedWeapon).

    burst_count = 3
    burst_delay_ms = 70          # интервал между выстрелами очереди, мс


class ShotgunWeapon(RangedWeapon):
    """Дробовик: 5 пуль веером за один выстрел - одна точно по центральной
    оси прицела, остальные симметрично расходятся по spread_angle_deg."""
    name = "Shotgun"
    weapon_id = "shotgun"
    color = (255, 110, 30)       # тёмно-оранжевая
    reach = 0
    damage = 1                   # за пульку - до 5 суммарно в упор
    duration_ms = 220
    cooldown_ms = 550            # медленнее и мощнее одиночного выстрела

    fires_projectile = True
    ammo_type = "bullets"
    magazine_size = 6
    projectile_speed = 460
    # Единственное оружие с ограничением дальности (см. RangedWeapon) - это
    # его штатный диапазон, дополнительно увеличенный на ~12%.
    projectile_max_range = 470   # было 420 (старый дефолт Rifle) * 1.12

    pellet_count = 5
    spread_angle_deg = 30        # ±15° от центральной оси прицела


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

    def get_attack_rects(self, player_rect, aim_dx, aim_dy):
        return [_rect_in_vector_direction(player_rect, aim_dx, aim_dy,
                                          self.reach, self.rect_width, self.rect_height)]


# Каталог всех доступных типов оружия по стабильному weapon_id.
# Порядок словаря = порядок отображения в InventoryScreen (см.
# PlayerCombat.set_slot_weapon). Единственный источник правды и для
# создания оружия по id (сохранения), и для стартовой раскладки.
WEAPON_CATALOG: Dict[str, Type[Weapon]] = {
    "sword": MeleeWeapon,
    "spear": PolearmWeapon,
    "rifle": RangedWeapon,
    "smg": BurstRifle,
    "shotgun": ShotgunWeapon,
    "bomb": AoeWeapon,
}


def create_weapon(weapon_id: str) -> Weapon:
    """Создать экземпляр оружия по стабильному id из WEAPON_CATALOG."""
    return WEAPON_CATALOG[weapon_id]()


def starting_slot_assignment() -> List[str]:
    """Стартовая раскладка слотов нового игрока: 2 слота, оба - мечи
    (ближний бой)."""
    return ["sword", "spear"]

