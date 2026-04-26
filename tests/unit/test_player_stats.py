"""
Тесты для PlayerStats — i-frames, XP, level-up, coins.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.entities.player_stats import PlayerStats, xp_for_next_level


class TestPlayerStatsIframes:

    def test_iframe_blocks_double_damage(self):
        """После получения урона повторный удар блокируется i-frames."""
        stats = PlayerStats(100)
        assert stats.take_damage(10)  # первый удар проходит
        assert stats.health == 90
        assert stats.iframe_timer > 0
        assert not stats.take_damage(10)  # второй блокируется
        assert stats.health == 90

    def test_iframe_expires_after_duration(self):
        """i-frame таймер истекает после нужного времени."""
        stats = PlayerStats(100)
        stats.take_damage(10)
        assert stats.is_invulnerable
        # Прокручиваем время
        stats.update(stats._iframe_duration + 0.01)
        assert not stats.is_invulnerable
        # Теперь можно получить урон
        assert stats.take_damage(10)
        assert stats.health == 80

    def test_ignore_iframes_bypasses(self):
        """ignore_iframes=True пробивает i-frames (terrain damage)."""
        stats = PlayerStats(100)
        stats.take_damage(10)
        assert stats.is_invulnerable
        assert stats.take_damage(5, ignore_iframes=True)
        assert stats.health == 85

    def test_dead_player_takes_no_damage(self):
        stats = PlayerStats(10)
        stats.take_damage(10)
        assert stats.is_dead()
        assert not stats.take_damage(5)


class TestPlayerStatsProgression:

    def test_xp_for_next_level_formula(self):
        """Формула XP монотонно растёт."""
        prev = 0
        for lvl in range(1, 20):
            xp = xp_for_next_level(lvl)
            assert xp > prev
            prev = xp

    def test_gain_xp_levels_up(self):
        """Набор XP >= порога поднимает уровень."""
        stats = PlayerStats(10)
        threshold = stats.xp_to_next_level
        levels = stats.gain_xp(threshold)
        assert levels == 1
        assert stats.level == 2
        assert stats.max_health == 10 + stats._hp_per_level

    def test_gain_xp_multiple_levels(self):
        """Большая порция XP может поднять несколько уровней."""
        stats = PlayerStats(10)
        levels = stats.gain_xp(10000)
        assert levels > 1
        assert stats.level > 2

    def test_max_level_cap(self):
        """Уровень не превышает max_level."""
        stats = PlayerStats(10)
        stats._max_level = 3
        stats.gain_xp(100000)
        assert stats.level == 3

    def test_heal_on_level_up(self):
        """При level-up HP восстанавливается до max."""
        stats = PlayerStats(10)
        stats.take_damage(5)
        stats.update(1.0)  # сбросить iframes
        assert stats.health == 5
        threshold = stats.xp_to_next_level
        stats.gain_xp(threshold)
        assert stats.health == stats.max_health

    def test_coins(self):
        stats = PlayerStats(10)
        assert stats.coins == 0
        stats.add_coins(5)
        assert stats.coins == 5
        stats.add_coins(3)
        assert stats.coins == 8

