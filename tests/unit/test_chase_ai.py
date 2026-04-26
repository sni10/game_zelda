"""
Тесты для ChaseBehavior — преследование игрока с возвратом на patrol.
"""
import math
import pygame
import pytest
from unittest.mock import MagicMock

from src.entities.enemy_ai import ChaseBehavior, PatrolBehavior


@pytest.fixture
def chase_ai():
    return ChaseBehavior(chase_radius=100, lose_radius=200)


@pytest.fixture
def enemy():
    e = MagicMock()
    e.x = 500.0
    e.y = 500.0
    e.rect = pygame.Rect(500, 500, 24, 24)
    e.stats = MagicMock()
    e.stats.speed = 80.0
    e.patrol_zone = pygame.Rect(400, 400, 200, 200)
    # PatrolBehavior uses hasattr check — disable auto-create
    del e._patrol_target
    del e._patrol_timer
    return e


@pytest.fixture
def world():
    w = MagicMock()
    w.check_collision.return_value = False
    return w


@pytest.fixture
def player_near():
    """Игрок внутри chase_radius."""
    p = MagicMock()
    p.x = 550.0
    p.y = 500.0
    return p


@pytest.fixture
def player_far():
    """Игрок далеко за lose_radius."""
    p = MagicMock()
    p.x = 900.0
    p.y = 900.0
    return p


class TestChaseBehavior:

    def test_enters_chase_when_player_in_radius(self, chase_ai, enemy, world, player_near):
        """Враг начинает преследование когда игрок рядом."""
        assert not chase_ai.is_chasing
        chase_ai.update(enemy, 0.1, world, player_near)
        assert chase_ai.is_chasing

    def test_loses_chase_when_player_far(self, chase_ai, enemy, world, player_near, player_far):
        """Враг теряет агро когда игрок уходит за lose_radius."""
        # Сначала начинаем преследование
        chase_ai.update(enemy, 0.1, world, player_near)
        assert chase_ai.is_chasing
        # Игрок далеко — теряем
        chase_ai.update(enemy, 0.1, world, player_far)
        assert not chase_ai.is_chasing

    def test_patrols_when_no_player(self, chase_ai, enemy, world):
        """Без игрока — просто патрулирует."""
        chase_ai.update(enemy, 0.1, world, None)
        assert not chase_ai.is_chasing

    def test_moves_toward_player_when_chasing(self, chase_ai, enemy, world, player_near):
        """При преследовании враг двигается к игроку."""
        old_x = enemy.x
        chase_ai.update(enemy, 0.5, world, player_near)
        # Игрок правее — враг должен сдвинуться вправо
        assert enemy.x > old_x

    def test_chase_respects_collision(self, chase_ai, enemy, world, player_near):
        """Враг не проходит сквозь стены при преследовании."""
        world.check_collision.return_value = True
        old_x = enemy.x
        old_y = enemy.y
        chase_ai.update(enemy, 0.5, world, player_near)
        # Позиция не изменилась — упёрся
        assert enemy.x == old_x
        assert enemy.y == old_y

