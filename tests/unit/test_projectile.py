"""
Тесты для Projectile / ProjectileManager (реальная баллистика Rifle, v0.4.0b).
"""
import os
import pytest
import pygame
from unittest.mock import MagicMock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
pygame.init()

from src.entities.projectile import Projectile
from src.systems.projectile_manager import ProjectileManager
from src.entities.enemy import Enemy, EnemyStats
from src.entities.enemy_ai import IdleBehavior


def _make_enemy(x=200, y=100, hp=1):
    stats = EnemyStats(
        name='Test', max_health=hp, speed=80,
        width=24, height=24, color=(200, 80, 80), damage=1,
    )
    zone = pygame.Rect(0, 0, 400, 400)
    return Enemy(x, y, stats, IdleBehavior(), zone)


class TestProjectileMovement:
    """Чистая механика движения/expiry, без ProjectileManager."""

    def test_moves_along_direction(self):
        p = Projectile(100, 100, 1.0, 0.0, speed=100, damage=1, max_range=1000)
        p.update(1.0)  # 1 сек при 100px/сек -> +100px по x
        assert p.x == pytest.approx(200)
        assert p.y == pytest.approx(100)

    def test_expires_at_max_range(self):
        p = Projectile(0, 0, 1.0, 0.0, speed=100, damage=1, max_range=50)
        assert not p.expired
        p.update(1.0)  # 100px пройдено > 50 max_range
        assert p.expired

    def test_stays_alive_before_max_range(self):
        p = Projectile(0, 0, 1.0, 0.0, speed=100, damage=1, max_range=1000)
        p.update(0.1)  # 10px << 1000
        assert not p.expired

    def test_draw_does_not_crash(self):
        screen = pygame.Surface((200, 200))
        p = Projectile(50, 50, 1.0, 0.0, speed=100, damage=1, max_range=100)
        p.draw(screen, 0, 0)

    def test_hitbox_is_5_percent_larger_than_visual_size(self):
        """Хитбокс (rect) намеренно чуть больше видимого круга (+5%) - более
        прощающие попадания без изменения того, что видит игрок."""
        assert Projectile.HITBOX_SIZE > Projectile.SIZE
        p = Projectile(50, 50, 1.0, 0.0, speed=100, damage=1, max_range=100)
        assert p.rect.width == Projectile.HITBOX_SIZE
        assert p.rect.height == Projectile.HITBOX_SIZE


@pytest.fixture
def world():
    w = MagicMock()
    w.width = 2000
    w.height = 2000
    w.check_collision.return_value = False
    w.enemy_manager.enemies = []
    return w


@pytest.fixture
def pm(world):
    return ProjectileManager(world)


class TestProjectileManagerCollision:
    """Столкновения снарядов с врагами/препятствиями/границами мира.

    update() делает единичную проверку позиции за кадр (без непрерывной
    развёртки/swept-коллизии) - поэтому попадание симулируется маленькими
    шагами dt, как в реальном игровом цикле (~1/60с за кадр), а не одним
    большим скачком, который мог бы "перепрыгнуть" врага.
    """

    def test_hits_enemy_and_returns_event(self, world, pm):
        enemy = _make_enemy(x=200, y=100, hp=1)
        world.enemy_manager.enemies = [enemy]
        proj = Projectile(100, 112, 1.0, 0.0, speed=500, damage=1, max_range=1000)
        pm.spawn(proj)

        events = []
        for _ in range(60):
            events = pm.update(1 / 60)
            if events:
                break

        assert len(events) == 1
        assert events[0]["damage"] == 1
        assert events[0]["killed"] is True
        assert pm.projectiles == []  # снаряд использован и удалён

    def test_does_not_hit_dead_enemy(self, world, pm):
        enemy = _make_enemy(x=200, y=100, hp=1)
        enemy.take_damage(1)
        assert enemy.is_dead()
        world.enemy_manager.enemies = [enemy]
        proj = Projectile(100, 112, 1.0, 0.0, speed=500, damage=1, max_range=1000)
        pm.spawn(proj)

        all_events = []
        for _ in range(60):
            all_events += pm.update(1 / 60)

        assert all_events == []

    def test_stops_at_obstacle(self, world, pm):
        world.check_collision.return_value = True
        proj = Projectile(100, 100, 1.0, 0.0, speed=100, damage=1, max_range=500)
        pm.spawn(proj)
        events = pm.update(0.1)
        assert events == []
        assert pm.projectiles == []

    def test_expires_out_of_world_bounds(self, world, pm):
        proj = Projectile(1990, 100, 1.0, 0.0, speed=1000, damage=1, max_range=5000)
        pm.spawn(proj)
        events = pm.update(1.0)
        assert events == []
        assert pm.projectiles == []

    def test_no_projectiles_no_crash(self, pm):
        assert pm.update(0.1) == []

    def test_draw_does_not_crash(self, world, pm):
        pm.spawn(Projectile(100, 100, 1.0, 0.0, speed=100, damage=1, max_range=500))
        screen = pygame.Surface((200, 200))
        pm.draw(screen, 0, 0)
