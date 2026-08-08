"""
Тесты для HUD: полоска щита брони (issue #63) не крашит отрисовку и
корректно отражает состояние PlayerStats/EquipmentSlots.
"""
import os

import pytest
import pygame

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
pygame.init()
pygame.display.set_mode((800, 600))

from src.core.config_loader import load_config
load_config()

from src.entities.player import Player
from src.ui.hud import HUD


@pytest.fixture()
def player():
    return Player(0, 0)


@pytest.fixture()
def hud():
    return HUD()


@pytest.fixture()
def screen():
    return pygame.Surface((1024, 768))


def test_draw_does_not_crash(hud, screen, player):
    hud.draw(screen, player)


def test_draw_with_no_player_is_noop(hud, screen):
    hud.draw(screen, None)


def test_draw_with_depleted_shield_does_not_crash(hud, screen, player):
    player.equipment.absorb_damage(player.max_shield)
    assert player.shield == 0
    hud.draw(screen, player)


def test_shield_bar_geometry_is_above_health_bar(hud):
    """Полоска щита должна оставаться выше полоски здоровья по Y."""
    assert hud.HEALTH_BAR_Y > 10
    assert hud.HEALTH_BAR_Y >= 10 + hud.SHIELD_BAR_HEIGHT
