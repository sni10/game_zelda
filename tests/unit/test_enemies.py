"""
Тесты системы врагов: HP, AI, фабрика, менеджер.
"""
import os
import math
import pytest
import pygame

# Без окна
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
pygame.init()

from src.core.config_loader import load_config
load_config()  # обязательно: статы врагов читаются из конфига

from src.entities.enemy import (
    Enemy, EnemyStats, LightEnemy, HeavyEnemy, FastEnemy,
)
from src.entities.enemy_ai import IdleBehavior, PatrolBehavior
from src.entities.enemy_factory import EnemyFactory, UnknownEnemyTypeError


# === Вспомогательные --------------------------------------------------------

def make_zone(cx=200, cy=200, radius=64):
    return pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)


def make_test_enemy(hp=3, x=200, y=200):
    """Простой Enemy для тестов HP/урона - без AI движения."""
    stats = EnemyStats(name='Test', max_health=hp, speed=0,
                      width=20, height=20, color=(255, 0, 0), damage=1)
    return Enemy(x, y, stats, IdleBehavior(), make_zone(x, y))


# === HP / урон / смерть -----------------------------------------------------

class TestEnemyHealth:
    def test_starts_at_max_health(self):
        e = make_test_enemy(hp=3)
        assert e.health == 3
        assert not e.is_dead()

    def test_take_damage_reduces_health(self):
        e = make_test_enemy(hp=3)
        e.take_damage(1)
        assert e.health == 2

    def test_dies_at_zero(self):
        e = make_test_enemy(hp=1)
        e.take_damage(1)
        assert e.is_dead()

    def test_overkill_clamps_to_zero(self):
        e = make_test_enemy(hp=2)
        e.take_damage(999)
        assert e.health == 0
        assert e.is_dead()

    def test_dead_enemy_does_not_update(self):
        """Мёртвый враг не должен двигаться."""
        e = make_test_enemy(hp=1)
        e.take_damage(1)
        old_x = e.x
        e.update(dt=1.0, world=None)  # world=None - дойдёт ли крэш?
        assert e.x == old_x


# === Patrol AI --------------------------------------------------------------

class TestPatrolBehavior:
    def test_patrol_stays_inside_zone(self):
        """100 кадров блуждания - враг не выходит за патруль-зону."""
        zone = make_zone(cx=500, cy=500, radius=128)
        stats = EnemyStats(name='P', max_health=1, speed=200,
                          width=16, height=16, color=(0, 0, 0), damage=1)
        ai = PatrolBehavior()
        # Спавним в центре зоны
        e = Enemy(500, 500, stats, ai, zone)

        # Mock world: коллизий нет
        class _W:
            def check_collision(self, rect):
                return False
        world = _W()

        for _ in range(200):
            e.update(dt=0.05, world=world)
            assert zone.left <= e.x <= zone.right - e.stats.width
            assert zone.top <= e.y <= zone.bottom - e.stats.height

    def test_patrol_repaths_on_collision(self):
        """Если упёрся в препятствие - перевыбирает цель."""
        zone = make_zone(cx=500, cy=500, radius=128)
        stats = EnemyStats(name='P', max_health=1, speed=400,
                          width=16, height=16, color=(0, 0, 0), damage=1)
        e = Enemy(500, 500, stats, PatrolBehavior(), zone)

        class _AlwaysBlocked:
            def check_collision(self, rect):
                return True
        # Один update - враг должен перевыбрать цель и НЕ двигаться
        old_x, old_y = e.x, e.y
        e.update(dt=0.1, world=_AlwaysBlocked())
        assert e.x == old_x and e.y == old_y


# === Фабрика ----------------------------------------------------------------

class TestEnemyFactory:
    def test_default_types_registered(self):
        """LightEnemy/HeavyEnemy/FastEnemy зарегистрированы при импорте."""
        types = EnemyFactory.registered_types()
        assert 'light' in types
        assert 'heavy' in types
        assert 'fast' in types

    def test_create_light(self):
        zone = make_zone()
        e = EnemyFactory.create('light', 100, 100, zone)
        assert isinstance(e, LightEnemy)
        assert e.health == 1  # из config

    def test_create_heavy(self):
        zone = make_zone()
        e = EnemyFactory.create('heavy', 100, 100, zone)
        assert isinstance(e, HeavyEnemy)
        assert e.health == 3

    def test_create_unknown_type_raises(self):
        with pytest.raises(UnknownEnemyTypeError):
            EnemyFactory.create('dragon', 0, 0, make_zone())

    def test_register_new_type(self):
        """Можно зарегистрировать новый тип без правки старого кода (OCP)."""
        # Кастомный фаб
        def make_boss(x, y, zone):
            stats = EnemyStats(name='Boss', max_health=100, speed=10,
                              width=64, height=64, color=(0, 0, 0), damage=50)
            return Enemy(x, y, stats, IdleBehavior(), zone)

        EnemyFactory.register('boss', make_boss)
        try:
            boss = EnemyFactory.create('boss', 0, 0, make_zone())
            assert boss.health == 100
            assert boss.stats.name == 'Boss'
        finally:
            # Чистим после теста
            EnemyFactory._registry.pop('boss', None)


# === Stats из конфига ------------------------------------------------------

class TestEnemyStatsFromConfig:
    def test_light_stats_match_config(self):
        e = LightEnemy.create(0, 0, make_zone())
        assert e.stats.max_health == 1
        assert e.stats.speed == 80.0

    def test_heavy_stats_match_config(self):
        e = HeavyEnemy.create(0, 0, make_zone())
        assert e.stats.max_health == 3
        assert e.stats.speed == 40.0
        assert e.stats.width == 40

    def test_fast_stats_match_config(self):
        e = FastEnemy.create(0, 0, make_zone())
        assert e.stats.speed == 160.0


# === EnemyManager - apply_player_attack ------------------------------------

class TestEnemyManagerCombat:
    """Главный инвариант: 1 атака игрока = 1 урон каждому врагу."""

    @pytest.fixture
    def manager(self):
        from src.systems.enemy_manager import EnemyManager

        # Простой mock world
        class _W:
            width = 2000
            height = 2000

            def check_collision(self, rect):
                return False
        m = EnemyManager(_W())
        # Один враг с 3 HP в позиции (200, 200) размером 20x20
        m.enemies.append(make_test_enemy(hp=3, x=200, y=200))
        return m

    def test_single_attack_damages_once(self, manager):
        """Один и тот же attack_id - враг получает урон только 1 раз."""
        target = manager.enemies[0]
        attack_rect = pygame.Rect(195, 195, 30, 30)  # покрывает врага

        h1, k1 = manager.apply_player_attack(attack_id=1, attack_rects=[attack_rect], damage=1)
        h2, k2 = manager.apply_player_attack(attack_id=1, attack_rects=[attack_rect], damage=1)
        h3, k3 = manager.apply_player_attack(attack_id=1, attack_rects=[attack_rect], damage=1)

        assert (h1, k1) == (1, 0)
        assert (h2, k2) == (0, 0)
        assert (h3, k3) == (0, 0)
        assert target.health == 2  # Один урон с 3 HP

    def test_new_attack_id_damages_again(self, manager):
        """Новая атака (новый ID) снова наносит урон."""
        target = manager.enemies[0]
        ar = pygame.Rect(195, 195, 30, 30)

        manager.apply_player_attack(attack_id=1, attack_rects=[ar], damage=1)
        manager.apply_player_attack(attack_id=2, attack_rects=[ar], damage=1)
        manager.apply_player_attack(attack_id=3, attack_rects=[ar], damage=1)

        assert target.is_dead()  # 3 удара по 1 HP

    def test_attack_misses_returns_zero(self, manager):
        """Если зона атаки не пересекает - 0 хитов."""
        ar = pygame.Rect(0, 0, 5, 5)  # далеко от врага в (200, 200)
        h, k = manager.apply_player_attack(attack_id=1, attack_rects=[ar], damage=10)
        assert (h, k) == (0, 0)

    def test_kill_counter(self, manager):
        """kills возвращается когда HP уходит в 0."""
        ar = pygame.Rect(195, 195, 30, 30)
        target = manager.enemies[0]
        h, k = manager.apply_player_attack(attack_id=1, attack_rects=[ar], damage=99)
        assert (h, k) == (1, 1)
        assert target.is_dead()

    def test_update_removes_dead(self, manager):
        """После update мёртвые враги удаляются."""
        ar = pygame.Rect(195, 195, 30, 30)
        manager.apply_player_attack(attack_id=1, attack_rects=[ar], damage=99)
        assert len(manager.enemies) == 1  # ещё в списке
        manager.update(dt=0.016)
        assert len(manager.enemies) == 0  # удалён


# === EnemyManager - спавн вне зоны видимости ------------------------------

class TestEnemyManagerSpawn:
    @pytest.fixture
    def manager(self):
        from src.systems.enemy_manager import EnemyManager

        class _W:
            width = 4000  # большой мир, чтобы было где спавнить вдали
            height = 4000

            def check_collision(self, rect):
                return False
        return EnemyManager(_W())

    def test_spawn_outside_visibility(self, manager):
        """Враг не должен появиться ближе spawn_min_distance от игрока."""
        from src.core.config_loader import get_config

        player_x, player_y = 2000, 2000
        min_dist = get_config('ENEMIES_SPAWN_MIN_DISTANCE')

        for _ in range(20):
            e = manager.spawn_enemy('light', player_x, player_y)
            assert e is not None
            d = math.hypot(e.x - player_x, e.y - player_y)
            assert d >= min_dist, f"Spawned at distance {d}, min was {min_dist}"

    def test_spawn_initial_counts(self, manager):
        """Спавнятся правильные количества по типам."""
        from src.core.config_loader import get_config

        manager.spawn_initial(player_x=2000, player_y=2000)
        by_type = manager.alive_by_type()

        assert by_type.get('light', 0) == get_config('ENEMIES_INITIAL_COUNT_LIGHT')
        assert by_type.get('heavy', 0) == get_config('ENEMIES_INITIAL_COUNT_HEAVY')
        assert by_type.get('fast', 0) == get_config('ENEMIES_INITIAL_COUNT_FAST')

