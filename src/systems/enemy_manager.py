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
from src.entities.pickup import HeartPickup, CoinPickup, XPOrbPickup


class EnemyManager:
    """Контейнер врагов для одного мира."""

    TILE_SIZE = 32  # размер тайла (для расчёта patrol_zone)

    def __init__(self, world, pickup_manager=None):
        self.world = world
        self.enemies: List[Enemy] = []
        self.pickup_manager = pickup_manager
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

    def update(self, dt: float, player_x: float = None, player_y: float = None,
               player=None) -> None:
        """Обновить AI всех живых врагов и удалить мёртвых.

        Если переданы координаты игрока - также периодически пытаемся
        восстановить численность убитых врагов (auto-respawn). Респавн
        соблюдает spawn_min_distance, поэтому игрок увидит "новых" врагов
        только когда отойдёт от зачищенной зоны.
        """
        for enemy in self.enemies:
            enemy.update(dt, self.world, player)
        # Drop loot с мёртвых ПЕРЕД удалением
        self._drop_loot_from_dead(player)
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
                            damage: int,
                            player=None) -> Tuple[int, int]:
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
        kb_speed = get_config('COMBAT_ENEMY_KNOCKBACK_SPEED', 180)
        kb_dur = get_config('COMBAT_ENEMY_KNOCKBACK_DURATION', 0.12)

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
                    # Knockback от игрока
                    if player is not None:
                        dx = enemy.x - player.x
                        dy = enemy.y - player.y
                        dist = math.hypot(dx, dy)
                        if dist < 1:
                            dx, dy, dist = 0, -1, 1
                        enemy.knockback_vx = (dx / dist) * kb_speed
                        enemy.knockback_vy = (dy / dist) * kb_speed
                        enemy.knockback_timer = kb_dur
                    hits += 1
                    if enemy.is_dead():
                        kills += 1
                    break  # одна атака - один урон врагу

        return (hits, kills)

    # --- Контактный урон врагов → игроку -----------------------------------

    def apply_contact_damage(self, player) -> int:
        """Проверить пересечение живых врагов с игроком и нанести контактный урон.

        Использует i-frames из PlayerStats: если игрок неуязвим — урон не наносится.
        Враг имеет свой attack_cooldown — не бьёт чаще чем раз в N секунд.
        При попадании: knockback игрока + retreat (отскок) врага.

        Возвращает суммарный нанесённый урон за этот кадр.
        """
        # i-frames check (делегируем PlayerStats)
        if player.is_invulnerable:
            return 0

        atk_cd = get_config('COMBAT_ENEMY_ATTACK_COOLDOWN', 1.2)
        retreat_speed = get_config('COMBAT_ENEMY_RETREAT_SPEED', 150)
        retreat_dur = get_config('COMBAT_ENEMY_RETREAT_DURATION', 0.2)

        total_damage = 0
        for enemy in self.enemies:
            if enemy.is_dead():
                continue
            # Враг на кулдауне — не бьёт
            if enemy.attack_cooldown_timer > 0:
                continue
            # Враг вплотную (touching_player) или прямо пересекается
            if enemy.touching_player or enemy.rect.colliderect(player.rect):
                dmg = enemy.stats.damage
                hit = player.take_damage(dmg)
                if hit:
                    # Knockback игрока от врага
                    player.apply_knockback(enemy.x, enemy.y)
                    # Retreat врага от игрока (отскок назад)
                    dx = enemy.x - player.x
                    dy = enemy.y - player.y
                    dist = math.hypot(dx, dy)
                    if dist < 1:
                        dx, dy, dist = 0, -1, 1
                    enemy.knockback_vx = (dx / dist) * retreat_speed
                    enemy.knockback_vy = (dy / dist) * retreat_speed
                    enemy.knockback_timer = retreat_dur
                    # Attack cooldown — враг не бьёт снова N секунд
                    enemy.attack_cooldown_timer = atk_cd
                    total_damage += dmg
                break  # один кадр = один удар

        return total_damage

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for enemy in self.enemies:
            enemy.draw(screen, camera_x, camera_y)

    # --- Drop loot ---------------------------------------------------------

    def _drop_loot_from_dead(self, player=None) -> None:
        """Спавнить пикапы с каждого только-что-умершего врага."""
        if self.pickup_manager is None:
            return
        for enemy in self.enemies:
            if not enemy.is_dead():
                continue
            # Уже дропнули? (помечаем атрибутом чтобы не дублировать)
            if getattr(enemy, '_loot_dropped', False):
                continue
            enemy._loot_dropped = True
            self._spawn_drops_for(enemy, player)

    def _spawn_drops_for(self, enemy, player=None) -> None:
        """Адаптивный дроп:
        - XP — всегда.
        - Сердечки — только если HP игрока неполное (по шансу).
        - Монеты — только если HP игрока полное (по шансу).
        Это создаёт интуитивную петлю: раненый игрок получает хил,
        здоровый — копит золото.
        """
        prefix = enemy.stats.name.lower()  # light / heavy / fast
        cx, cy = enemy.x, enemy.y

        # XP — всегда (фиксированное количество)
        xp_amount = get_config(f'DROPS_{prefix.upper()}_XP_AMOUNT', 0)
        if xp_amount > 0:
            self.pickup_manager.spawn(
                XPOrbPickup(cx + random.uniform(-8, 8),
                            cy + random.uniform(-8, 8))
            )

        # Определяем что дропать: сердечки или монеты
        player_needs_heal = (
            player is not None
            and player.health < player.max_health
        )

        if player_needs_heal:
            # Сердечко — шанс (только при неполном HP)
            heart_chance = get_config(f'DROPS_{prefix.upper()}_HEART_CHANCE', 0.0)
            if random.random() < heart_chance:
                self.pickup_manager.spawn(
                    HeartPickup(cx + random.uniform(-8, 8),
                                cy + random.uniform(-8, 8))
                )
        else:
            # Монеты — шанс + случайное количество (только при полном HP)
            coin_chance = get_config(f'DROPS_{prefix.upper()}_COIN_CHANCE', 0.0)
            if random.random() < coin_chance:
                coin_min = get_config(f'DROPS_{prefix.upper()}_COIN_MIN', 1)
                coin_max = get_config(f'DROPS_{prefix.upper()}_COIN_MAX', 1)
                count = random.randint(coin_min, coin_max)
                for _ in range(count):
                    self.pickup_manager.spawn(
                        CoinPickup(cx + random.uniform(-12, 12),
                                   cy + random.uniform(-12, 12))
                    )

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

    # --- Сериализация ------------------------------------------------------

    def serialize(self) -> dict:
        """Сохранить живых врагов с HP/позицией + target_counts для респавна."""
        enemies_data = []
        for e in self.enemies:
            if e.is_dead():
                continue
            enemies_data.append({
                "type": e.stats.name.lower(),  # 'light' / 'heavy' / 'fast'
                "x": float(e.x),
                "y": float(e.y),
                "health": int(e.health),
                "attack_cooldown_timer": float(e.attack_cooldown_timer),
            })
        return {
            "enemies": enemies_data,
            "target_counts": dict(self.target_counts),
            "respawn_timer": float(self._respawn_timer),
        }

    def deserialize(self, data: dict) -> None:
        """Восстановить врагов и параметры респавна (заменяет текущих)."""
        self.enemies = []
        if not data:
            return
        for item in data.get("enemies", []):
            type_id = item.get("type")
            x = float(item.get("x", 0))
            y = float(item.get("y", 0))
            cx = x + self.TILE_SIZE / 2
            cy = y + self.TILE_SIZE / 2
            patrol_zone = self._make_patrol_zone(cx, cy)
            try:
                enemy = EnemyFactory.create(type_id, x, y, patrol_zone)
            except Exception:
                continue
            enemy.health = int(item.get("health", enemy.stats.max_health))
            enemy.attack_cooldown_timer = float(item.get("attack_cooldown_timer", 0))
            self.enemies.append(enemy)
        self.target_counts = dict(data.get("target_counts", {}))
        self._respawn_timer = float(data.get("respawn_timer", 0.0))

