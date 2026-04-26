"""
Тесты системы оружий.

Покрывают:
- Симметричность зон поражения по 8 направлениям (фикс старого бага,
  где down/right были впритык, а up/left имели зазор).
- Параметризацию reach для разных типов оружия.
- Множественные зоны (RangedWeapon - "трасса стрелы").
- Переключение оружий в Player.switch_weapon().
"""
import os
import pytest
import pygame

from src.entities.weapons import (
    MeleeWeapon, PolearmWeapon, RangedWeapon, AoeWeapon,
    DIRECTION_VECTORS, _rect_in_direction,
)


# Тесты не должны открывать окно
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
pygame.init()


@pytest.fixture
def player_rect():
    """Игрок 32x32 в позиции (100, 100)."""
    return pygame.Rect(100, 100, 32, 32)


# --- Симметрия (главный фикс бага) -----------------------------------------

class TestSymmetry:
    """Раньше down/right были впритык, а up/left - с зазором.
    Теперь все 8 направлений симметричны через _rect_in_direction()."""

    @pytest.mark.parametrize("reach,size", [(0, 32), (16, 32), (32, 32)])
    def test_horizontal_pair_symmetric(self, player_rect, reach, size):
        """Зазор слева = зазор справа."""
        left = _rect_in_direction(player_rect, 'left', reach, size, size)
        right = _rect_in_direction(player_rect, 'right', reach, size, size)

        gap_left = player_rect.left - left.right
        gap_right = right.left - player_rect.right

        assert gap_left == gap_right == reach, (
            f"reach={reach}: gap_left={gap_left}, gap_right={gap_right}"
        )

    @pytest.mark.parametrize("reach,size", [(0, 32), (16, 32), (32, 32)])
    def test_vertical_pair_symmetric(self, player_rect, reach, size):
        """Зазор сверху = зазор снизу."""
        up = _rect_in_direction(player_rect, 'up', reach, size, size)
        down = _rect_in_direction(player_rect, 'down', reach, size, size)

        gap_up = player_rect.top - up.bottom
        gap_down = down.top - player_rect.bottom

        assert gap_up == gap_down == reach, (
            f"reach={reach}: gap_up={gap_up}, gap_down={gap_down}"
        )

    def test_all_directions_present(self, player_rect):
        """Базовый sanity: для всех 8 направлений рассчитывается rect."""
        for direction in DIRECTION_VECTORS:
            r = _rect_in_direction(player_rect, direction, 0, 32, 32)
            assert isinstance(r, pygame.Rect)

    def test_diagonals_symmetric(self, player_rect):
        """Диагональные пары симметричны относительно центра игрока."""
        ul = _rect_in_direction(player_rect, 'up_left', 0, 32, 32)
        dr = _rect_in_direction(player_rect, 'down_right', 0, 32, 32)
        ur = _rect_in_direction(player_rect, 'up_right', 0, 32, 32)
        dl = _rect_in_direction(player_rect, 'down_left', 0, 32, 32)

        cx, cy = player_rect.center
        # ul и dr - зеркальная пара относительно центра
        assert (ul.centerx - cx) == -(dr.centerx - cx)
        assert (ul.centery - cy) == -(dr.centery - cy)
        # ur и dl - тоже
        assert (ur.centerx - cx) == -(dl.centerx - cx)
        assert (ur.centery - cy) == -(dl.centery - cy)


# --- Поведение конкретных оружий -------------------------------------------

class TestMeleeWeapon:
    """Меч: впритык, reach=0."""

    def test_no_gap(self, player_rect):
        sword = MeleeWeapon()
        assert sword.reach == 0
        rect = sword.get_attack_rects(player_rect, 'right')[0]
        # Зона начинается ровно на правом ребре игрока
        assert rect.left == player_rect.right

    def test_returns_single_rect(self, player_rect):
        rects = MeleeWeapon().get_attack_rects(player_rect, 'up')
        assert len(rects) == 1


class TestPolearmWeapon:
    """Копьё: с отступом полклетки."""

    def test_half_tile_gap(self, player_rect):
        spear = PolearmWeapon()
        assert spear.reach == 16
        rect = spear.get_attack_rects(player_rect, 'right')[0]
        gap = rect.left - player_rect.right
        assert gap == 16


class TestRangedWeapon:
    """Лук: возвращает несколько Rect (трасса стрелы)."""

    def test_multiple_rects(self, player_rect):
        bow = RangedWeapon()
        rects = bow.get_attack_rects(player_rect, 'right')
        assert len(rects) == bow.trace_length == 3

    def test_rects_are_consecutive(self, player_rect):
        """Каждая следующая клетка трассы дальше предыдущей."""
        rects = RangedWeapon().get_attack_rects(player_rect, 'right')
        # Проверяем монотонное удаление от игрока по направлению
        cx = player_rect.centerx
        distances = [abs(r.centerx - cx) for r in rects]
        assert distances == sorted(distances)
        assert distances[0] < distances[-1]


class TestAoeWeapon:
    """Бомба: одна большая зона 3x3 клетки."""

    def test_large_area(self, player_rect):
        bomb = AoeWeapon()
        rect = bomb.get_attack_rects(player_rect, 'right')[0]
        assert rect.width == 96
        assert rect.height == 96


# --- Интеграция с Player ---------------------------------------------------

class TestPlayerWeaponSwitching:
    """Player должен корректно переключать оружия."""

    @pytest.fixture
    def player(self):
        from src.entities.player import Player
        return Player(100, 100)

    def test_default_weapon_is_first(self, player):
        assert player.current_weapon_index == 0
        assert isinstance(player.current_weapon, MeleeWeapon)

    def test_switch_to_polearm(self, player):
        assert player.switch_weapon(1) is True
        assert isinstance(player.current_weapon, PolearmWeapon)

    def test_switch_to_invalid_index_rejected(self, player):
        assert player.switch_weapon(99) is False
        assert player.current_weapon_index == 0

    def test_switch_during_attack_rejected(self, player):
        player.attacking = True
        assert player.switch_weapon(1) is False
        assert player.current_weapon_index == 0

    def test_switch_to_same_weapon_returns_false(self, player):
        # Уже на 0 - повторный выбор 0 не считается переключением
        assert player.switch_weapon(0) is False

