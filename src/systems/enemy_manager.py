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
        # Целевое количество врагов по типам - устанавливается при
        # spawn_initial(). Используется для авто-респавна: когда игрок
        # уходит далеко и убитые враги "забываются", новые появляются
        # чтобы восстановить численность.
        self.target_counts: dict = {}
        # Таймер до следующей попытки респавна (секунды)
        self._respawn_timer = 0.0
        # Координаты игрока обновляются из update() - нужны для проверки
        # минимальной дистанции при респавне.
        self._last_player_pos = (0.0, 0.0)

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
        Возвращает количество реально созданных.

        Запоминает целевые количества для последующего авто-респавна.
        """
        targets = {
            'light': get_config('ENEMIES_INITIAL_COUNT_LIGHT'),
            'heavy': get_config('ENEMIES_INITIAL_COUNT_HEAVY'),
            'fast':  get_config('ENEMIES_INITIAL_COUNT_FAST'),
        }
        # Сохраняем для респавна
        self.target_counts = dict(targets)

        total_spawned = 0
        for type_id, count in targets.items():
            for _ in range(count):
                if self.spawn_enemy(type_id, player_x, player_y) is not None:
                    total_spawned += 1
        return total_spawned

    # --- Респавн -----------------------------------------------------------

    def _try_respawn_missing(self, player_x: float, player_y: float) -> int:
        """Попытаться доспавнить врагов до target_counts.

        Учитывает spawn_min_distance - значит респавн произойдёт ТОЛЬКО
        в зонах, удалённых от игрока. То есть пока игрок стоит в зачищенной
        области, новые враги там не появятся - только когда отойдёт.

        Возвращает количество реально заспавненных врагов.
        """
        if not self.target_counts:
            return 0

        current = self.alive_by_type()
        spawned = 0
        for type_id, target in self.target_counts.items():
            missing = target - current.get(type_id, 0)
            for _ in range(missing):
                if self.spawn_enemy(type_id, player_x, player_y) is not None:
                    spawned += 1
        return spawned

    # --- Обновление --------------------------------------------------------

    def update(self, dt: float, player_x: float = None, player_y: float = None) -> None:
        """Обновить AI всех живых врагов и удалить мёртвых.

        Если переданы координаты игрока - также периодически пытаемся
        восстановить численность убитых врагов (auto-respawn). Респавн
        соблюдает spawn_min_distance, поэтому игрок увидит "новых" врагов
        только когда отойдёт от зачищенной зоны.
        """
        for enemy in self.enemies:
            enemy.update(dt, self.world)
        # Чистим мёртвых
        self.enemies = [e for e in self.enemies if not e.is_dead()]

        # Авто-респавн (опционально - если переданы координаты игрока)
        if player_x is not None and player_y is not None:
            self._last_player_pos = (player_x, player_y)
            self._respawn_timer -= dt
            if self._respawn_timer <= 0:
                # Сброс таймера ДО спавна (не зациклиться даже если нет места)
                try:
                    self._respawn_timer = float(get_config('ENEMIES_RESPAWN_INTERVAL'))
                except KeyError:
                    self._respawn_timer = 5.0  # default
                self._try_respawn_missing(player_x, player_y)

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

    # --- Контактный урон врагов → игроку -----------------------------------

    def apply_contact_damage(self, player) -> int:
        """Проверить пересечение живых врагов с игроком и нанести контактный урон.

        Урон берётся из enemy.stats.damage. Каждый кадр каждый пересекающийся
        враг наносит урон (но player.damage_cooldown ограничивает частоту
        получения урона от окружения - по аналогии с болотом/песком).

        Возвращает суммарный нанесённый урон за этот кадр.
        """
        total_damage = 0
        current_time = pygame.time.get_ticks()

        # Проверяем cooldown на стороне игрока (чтобы не дамажило каждый кадр)
        if current_time - player.last_damage_time < player.damage_cooldown:
            return 0

        for enemy in self.enemies:
            if enemy.is_dead():
                continue
            if enemy.rect.colliderect(player.rect):
                dmg = enemy.stats.damage
                player.take_damage(dmg)
                player.last_damage_time = current_time
                total_damage += dmg
                break  # один кадр = один удар (первый враг в списке)

        return total_damage

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

