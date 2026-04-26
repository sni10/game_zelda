"""
Тесты для Pickup и PickupManager.
"""
import pytest
import pygame
from unittest.mock import MagicMock, patch

from src.entities.pickup import HeartPickup, CoinPickup, XPOrbPickup
from src.systems.pickup_manager import PickupManager


@pytest.fixture
def player():
    p = MagicMock()
    p.x = 100.0
    p.y = 100.0
    p.width = 32
    p.height = 32
    p.rect = pygame.Rect(100, 100, 32, 32)
    p.stats = MagicMock()
    p.stats.health = 5
    p.stats.max_health = 10
    p.stats.coins = 0
    p.stats.xp = 0
    return p


class TestHeartPickup:

    def test_heart_heals(self, player):
        """HeartPickup вызывает player.heal()."""
        hp = HeartPickup(105.0, 105.0)
        hp.apply(player)
        player.heal.assert_called_once()

    def test_heart_collected_on_collision(self, player):
        """Пикап собирается при коллизии с игроком."""
        hp = HeartPickup(100.0, 100.0)
        hp.update(0.1, player)
        assert hp.collected


class TestCoinPickup:

    def test_coin_adds_coins(self, player):
        """CoinPickup добавляет монету."""
        cp = CoinPickup(100.0, 100.0)
        cp.apply(player)
        player.stats.add_coins.assert_called_once()


class TestXPOrbPickup:

    def test_xp_orb_grants_xp(self, player):
        """XPOrbPickup даёт XP."""
        xp = XPOrbPickup(100.0, 100.0)
        xp.apply(player)
        player.stats.gain_xp.assert_called_once()


class TestPickupManager:

    def test_spawn_adds_pickup(self):
        pm = PickupManager()
        p = HeartPickup(0, 0)
        pm.spawn(p)
        assert pm.count() == 1

    def test_lifetime_expires(self, player):
        """Пикап исчезает когда lifetime истекает."""
        pm = PickupManager()
        p = HeartPickup(999.0, 999.0)  # Далеко от игрока
        p.lifetime = 0.5
        pm.spawn(p)
        # Обновляем на 1 сек — дольше lifetime
        pm.update(1.0, player)
        assert pm.count() == 0

    def test_magnet_pulls_within_radius(self, player):
        """Пикап притягивается когда в радиусе магнита."""
        # Располагаем пикап рядом с игроком (в пределах magnet_radius=60)
        px = player.x + 40
        py = player.y
        p = CoinPickup(px, py)
        p.lifetime = 999
        old_x = p.x
        # Один тик — пикап должен сдвинуться к игроку
        p.update(0.1, player)
        # Если коллизия не произошла, x должен уменьшиться (к игроку)
        # Но при dist < magnet_radius и коллизии — собирается
        # В нашем случае dist=40 < 60, значит магнит работает
        assert p.x != old_x or p.collected

