"""
Тесты энергощита врагов (issue #63).

Покрывают:
- Щит поглощает попадания целиком, пока не разбит - HP не трогается.
- После разрушения щита урон идёт в HP как раньше.
- Реген щита по таймауту простоя, сброс таймера при новом попадании.
- Враги без щита (shield_max_hits=0) ведут себя как раньше (совместимость).
"""

import os

import pygame
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.core.config_loader import load_config
from src.entities.enemy import Enemy, EnemyStats, LightEnemy, HeavyEnemy, FastEnemy
from src.entities.enemy_ai import PatrolBehavior


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    # Не вызываем pygame.quit() в teardown - другие тестовые модули держат
    # синглтон-хэндлы (например src/utils/debug.py: font создаётся один раз
    # на уровне модуля), quit() их инвалидирует и роняет полный прогон
    # тестов access violation при следующем использовании.
    pygame.init()
    load_config()
    yield


def _make_enemy(max_health=10, shield_max_hits=0, shield_regen_timeout=5.0):
    stats = EnemyStats(
        name="Test",
        max_health=max_health,
        speed=50.0,
        width=32,
        height=32,
        color=(255, 0, 0),
        damage=1,
        shield_max_hits=shield_max_hits,
        shield_regen_timeout=shield_regen_timeout,
    )
    zone = pygame.Rect(0, 0, 500, 500)
    return Enemy(100, 100, stats, PatrolBehavior(), zone)


# --- No shield (backward compat) ------------------------------------------


class TestNoShield:
    def test_damage_goes_directly_to_health(self):
        e = _make_enemy(max_health=10, shield_max_hits=0)
        e.take_damage(4)
        assert e.health == 6
        assert e.shield_hits_remaining == 0

    def test_dies_at_zero_health(self):
        e = _make_enemy(max_health=5, shield_max_hits=0)
        e.take_damage(5)
        assert e.is_dead() is True


# --- Shield absorbs hits ---------------------------------------------------


class TestShieldAbsorption:
    def test_shield_starts_full(self):
        e = _make_enemy(shield_max_hits=3)
        assert e.shield_hits_remaining == 3

    def test_hit_while_shield_up_does_not_touch_health(self):
        e = _make_enemy(max_health=10, shield_max_hits=3)
        e.take_damage(
            999
        )  # amount is irrelevant while shield holds - "hits" not points
        assert e.health == 10
        assert e.shield_hits_remaining == 2

    def test_shield_depletes_after_max_hits(self):
        e = _make_enemy(max_health=10, shield_max_hits=3)
        e.take_damage(1)
        e.take_damage(1)
        e.take_damage(1)
        assert e.shield_hits_remaining == 0
        assert e.health == 10  # still untouched, that was the 3rd shield hit

    def test_damage_reaches_health_once_shield_is_broken(self):
        e = _make_enemy(max_health=10, shield_max_hits=1)
        e.take_damage(1)  # breaks shield
        assert e.shield_hits_remaining == 0
        assert e.health == 10
        e.take_damage(4)  # now hits HP
        assert e.health == 6

    def test_shield_can_kill_via_health_after_broken(self):
        e = _make_enemy(max_health=3, shield_max_hits=1)
        e.take_damage(1)  # breaks shield only
        assert e.is_dead() is False
        e.take_damage(3)
        assert e.is_dead() is True


# --- Shield regen ------------------------------------------------------


class TestShieldRegen:
    def test_regen_after_timeout_with_no_further_damage(self):
        e = _make_enemy(max_health=10, shield_max_hits=2, shield_regen_timeout=1.0)
        e.take_damage(1)
        assert e.shield_hits_remaining == 1
        e.update(1.0, world=None, player=None)
        assert e.shield_hits_remaining == 2

    def test_no_regen_before_timeout_elapses(self):
        e = _make_enemy(max_health=10, shield_max_hits=2, shield_regen_timeout=5.0)
        e.take_damage(1)
        e.update(2.0, world=None, player=None)
        assert e.shield_hits_remaining == 1

    def test_taking_damage_resets_regen_timer(self):
        e = _make_enemy(max_health=10, shield_max_hits=2, shield_regen_timeout=5.0)
        e.take_damage(1)
        e.update(4.0, world=None, player=None)  # almost regen'd
        e.take_damage(1)  # shield now fully broken, timer resets
        assert e.shield_hits_remaining == 0
        e.update(4.0, world=None, player=None)  # would've regen'd if timer hadn't reset
        assert e.shield_hits_remaining == 0
        e.update(1.0, world=None, player=None)  # total 5.0s since last hit
        assert e.shield_hits_remaining == 2

    def test_regen_is_noop_once_full(self):
        e = _make_enemy(max_health=10, shield_max_hits=2, shield_regen_timeout=1.0)
        e.update(10.0, world=None, player=None)
        assert e.shield_hits_remaining == 2

    def test_dead_enemy_does_not_regen(self):
        e = _make_enemy(max_health=1, shield_max_hits=0)
        e.take_damage(1)
        assert e.is_dead() is True
        e.shield_hits_remaining = 0
        e.update(100.0, world=None, player=None)  # should early-return, no crash


# --- Config-backed enemy types (issue #63 balance values) -----------------


class TestConfiguredEnemyShields:
    """light/fast: 1 shield hit, heavy: 3 - см. config.ini [enemies]."""

    def test_light_and_fast_have_single_shield_hit(self):
        zone = pygame.Rect(0, 0, 500, 500)
        light = LightEnemy.create(0, 0, zone)
        fast = FastEnemy.create(0, 0, zone)
        assert light.stats.shield_max_hits == 1
        assert fast.stats.shield_max_hits == 1

    def test_heavy_has_three_shield_hits(self):
        zone = pygame.Rect(0, 0, 500, 500)
        heavy = HeavyEnemy.create(0, 0, zone)
        assert heavy.stats.shield_max_hits == 3

    def test_light_enemy_hp_bar_visible_even_at_full_health(self):
        """Регрессия: раньше HP-бар рисовался только при health < max_health,
        из-за чего у 1-HP врагов бар был почти не виден. Теперь отрисовка
        всегда идёт по фактическому health/max_health - при полном HP
        fill_w == bar_w (бар виден, просто заполнен целиком)."""
        zone = pygame.Rect(0, 0, 500, 500)
        light = LightEnemy.create(0, 0, zone)
        assert light.health == light.stats.max_health
        fill_w = int(light.stats.width * light.health / light.stats.max_health)
        assert fill_w == light.stats.width
