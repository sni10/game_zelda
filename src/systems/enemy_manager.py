"""
EnemyManager - управление всеми врагами в мире.

Обязанности:
- Хранение списка живых врагов
- Спавн врагов вне зоны видимости игрока (через config)
- Обновление AI каждый кадр
- Применение урона от атаки игрока с защитой от множественных хитов
- Удаление мёртвых врагов
- Отрисовка всех видимых врагов
"""
import math
import random
from typing import List, Tuple

import pygame

from src.core.config_loader import get_config
from src.entities.enemy import Enemy
from src.entities.enemy_factory import EnemyFactory


class EnemyManager:
    """Контейнер врагов для одного мира."""

    TILE_SIZE = 32  # размер тайла (для расчёта patrol_zone)

    def __init__(self, world):
        self.world = world
        self.enemies: List[Enemy] = []

    # --- Спавн -------------------------------------------------------------

    def _make_patrol_zone(self, cx: float, cy: float) -> pygame.Rect:
        """Построить квадрат патрулирования (radius_tiles*2 x radius_tiles*2)
        вокруг точки (cx, cy)."""
        radius = get_config('ENEMIES_PATROL_RADIUS_TILES') * self.TILE_SIZE
        return pygame.Rect(
            int(cx - radius), int(cy - radius),
            radius * 2, radius * 2,
        )

    def _is_valid_spawn_point(self, x: float, y: float, size: int,
                              player_x: float, player_y: float,
                              min_distance: float) -> bool:
        """Проверить что точка спавна:
        - в пределах мира
        - проходима (не пересекает obstacles)
        - дальше min_distance от игрока (вне зоны видимости)
        """
        # В мире
        if x < 0 or y < 0:
            return False
        if x + size > self.world.width or y + size > self.world.height:
            return False
        # Не на препятствии
        candidate = pygame.Rect(int(x), int(y), size, size)
        if self.world.check_collision(candidate):
            return False
        # Дальше игрока на min_distance
        dx = x - player_x
        dy = y - player_y
        return math.hypot(dx, dy) >= min_distance

    def spawn_enemy(self, type_id: str, player_x: float, player_y: float) -> Enemy:
        """Создать одного врага типа type_id в случайной валидной точке.

        Возвращает созданного врага (уже добавлен в self.enemies)
        или None если не нашли точку за max_attempts попыток.
        """
        # Размер врага нужен заранее для проверки коллизий - создаём
        # временный Enemy чтобы прочитать размер из его статов.
        # Cheaper: используем константный максимум size из конфига.
        size_key = f'ENEMIES_{type_id.upper()}_SIZE'
        size = get_config(size_key)

        min_distance = get_config('ENEMIES_SPAWN_MIN_DISTANCE')
        max_attempts = get_config('ENEMIES_SPAWN_MAX_ATTEMPTS')
        radius_px = get_config('ENEMIES_PATROL_RADIUS_TILES') * self.TILE_SIZE

        for _ in range(max_attempts):
            x = random.uniform(radius_px, self.world.width - radius_px - size)
            y = random.uniform(radius_px, self.world.height - radius_px - size)

            if self._is_valid_spawn_point(x, y, size, player_x, player_y, min_distance):
                cx = x + size / 2
                cy = y + size / 2
                patrol_zone = self._make_patrol_zone(cx, cy)
                enemy = EnemyFactory.create(type_id, x, y, patrol_zone)
                self.enemies.append(enemy)
                return enemy

        return None

    def spawn_initial(self, player_x: float, player_y: float) -> int:
        """Заспавнить врагов согласно initial_count_* из конфига.
        Возвращает количество реально созданных."""
        targets = {
            'light': get_config('ENEMIES_INITIAL_COUNT_LIGHT'),
            'heavy': get_config('ENEMIES_INITIAL_COUNT_HEAVY'),
            'fast':  get_config('ENEMIES_INITIAL_COUNT_FAST'),
        }
        total_spawned = 0
        for type_id, count in targets.items():
            for _ in range(count):
                if self.spawn_enemy(type_id, player_x, player_y) is not None:
                    total_spawned += 1
        return total_spawned

    # --- Обновление --------------------------------------------------------

    def update(self, dt: float) -> None:
        """Обновить AI всех живых врагов и удалить мёртвых."""
        for enemy in self.enemies:
            enemy.update(dt, self.world)
        # Чистим мёртвых
        self.enemies = [e for e in self.enemies if not e.is_dead()]

    # --- Урон от атаки игрока ---------------------------------------------

    def apply_player_attack(self, attack_id: int,
                            attack_rects: List[pygame.Rect],
                            damage: int) -> Tuple[int, int]:
        """Нанести урон врагам, которых задевают зоны атаки.

        attack_id - уникальный идентификатор текущей атаки игрока,
                    нужен чтобы не наносить урон одной атакой каждый кадр.
                    Один враг получит урон от одной atак_id максимум один раз.

        Возвращает (hits, kills).
        """
        if not attack_rects:
            return (0, 0)

        hits = 0
        kills = 0

        for enemy in self.enemies:
            if enemy.is_dead():
                continue
            # Этот враг уже был задет этой атакой - пропускаем
            if enemy.last_hit_attack_id == attack_id:
                continue
            # Любая из зон атаки попадает по врагу?
            for r in attack_rects:
                if r.colliderect(enemy.rect):
                    enemy.take_damage(damage)
                    enemy.last_hit_attack_id = attack_id
                    hits += 1
                    if enemy.is_dead():
                        kills += 1
                    break  # одна атака - один урон врагу

        return (hits, kills)

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for enemy in self.enemies:
            enemy.draw(screen, camera_x, camera_y)

    # --- Утилиты -----------------------------------------------------------

    def alive_count(self) -> int:
        return sum(1 for e in self.enemies if not e.is_dead())

    def alive_by_type(self) -> dict:
        """Сколько живых врагов каждого type_id."""
        result = {}
        for e in self.enemies:
            if not e.is_dead():
                tid = e.stats.name.lower()
                result[tid] = result.get(tid, 0) + 1
        return result

