"""
Тесты системы оружий.

Покрывают:
- Симметричность зон поражения по 8 направлениям (фикс старого бага,
  где down/right были впритык, а up/left имели зазор).
- Параметризацию reach для разных типов оружия.
- RangedWeapon (Rifle) - реальная баллистика через Projectile, не мгновенный rect.
- Переключение оружий в Player.switch_weapon().
"""
import os
import pytest
import pygame

from src.entities.weapons import (
    MeleeWeapon, PolearmWeapon, RangedWeapon, AoeWeapon,
    DIRECTION_VECTORS, _rect_in_direction,
    WEAPON_CATALOG, create_weapon, starting_slot_assignment,
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
    """Rifle: реальная баллистика (Projectile), не мгновенный rect."""

    def test_no_instant_attack_rects(self, player_rect):
        """Урон наносит Projectile, get_attack_rects() пуст (иначе
        Player.draw() рисовал бы поверх летящей пули старую рамку)."""
        rifle = RangedWeapon()
        assert rifle.get_attack_rects(player_rect, 'right') == []

    def test_fires_projectile_flag(self):
        assert RangedWeapon.fires_projectile is True
        assert RangedWeapon.ammo_type == "bullets"
        assert RangedWeapon.magazine_size > 0
        assert RangedWeapon.projectile_speed > 0
        assert RangedWeapon.projectile_max_range > 0

    def test_melee_weapons_do_not_fire_projectiles(self):
        assert MeleeWeapon.fires_projectile is False
        assert PolearmWeapon.fires_projectile is False
        assert AoeWeapon.fires_projectile is False
        assert MeleeWeapon.ammo_type is None
        assert PolearmWeapon.ammo_type is None
        assert AoeWeapon.ammo_type is None


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


# --- Каталог оружия и стабильные id -----------------------------------------

class TestWeaponCatalog:
    """WEAPON_CATALOG - единственный источник правды для id/создания оружия."""

    def test_catalog_ids(self):
        assert set(WEAPON_CATALOG) == {"sword", "spear", "rifle", "bomb"}

    def test_create_weapon_by_id(self):
        w = create_weapon("rifle")
        assert isinstance(w, RangedWeapon)
        assert w.weapon_id == "rifle"
        assert w.category == "ranged"

    def test_weapon_categories(self):
        assert MeleeWeapon.category == "melee"
        assert PolearmWeapon.category == "melee"
        assert RangedWeapon.category == "ranged"
        assert AoeWeapon.category == "ranged"

    def test_starting_slot_assignment_is_two_melee(self):
        assert starting_slot_assignment() == ["sword", "spear"]


# --- Гибкие слоты (2 -> 8 по уровню, свободное назначение) ------------------

class TestFlexibleWeaponSlots:
    """PlayerCombat.unlock_slot / cycle_slot_weapon (см. player_combat.py)."""

    @pytest.fixture
    def player(self):
        from src.entities.player import Player
        return Player(100, 100)

    def test_starts_with_two_slots(self, player):
        assert len(player.weapons) == 2
        assert [w.weapon_id for w in player.weapons] == ["sword", "spear"]

    def test_unlock_slot_grows_list(self, player):
        assert player.unlock_slot() is True
        assert len(player.weapons) == 3

    def test_unlock_slot_capped_at_eight(self, player):
        for _ in range(10):
            player.unlock_slot()
        assert len(player.weapons) == 8
        assert player.unlock_slot() is False

    def test_cycle_slot_weapon_advances_catalog_order(self, player):
        assert player.weapons[0].weapon_id == "sword"
        assert player.cycle_slot_weapon(0) is True
        assert player.weapons[0].weapon_id == "spear"

    def test_cycle_wraps_around_full_catalog(self, player):
        # sword -> spear -> rifle -> bomb -> sword (4 записи в каталоге)
        for _ in range(len(WEAPON_CATALOG)):
            player.cycle_slot_weapon(0)
        assert player.weapons[0].weapon_id == "sword"

    def test_cycle_blocked_during_attack(self, player):
        player.attacking = True
        assert player.cycle_slot_weapon(0) is False

    def test_cycle_out_of_range_rejected(self, player):
        assert player.cycle_slot_weapon(5) is False  # слот ещё не разлочен

    def test_switch_to_locked_slot_rejected(self, player):
        # Только 2 слота есть - индекс 2 ещё не существует
        assert player.switch_weapon(2) is False


class TestWeaponSlotUnlockOnLevelUp:
    """Разлочка слотов должна следовать config.ini weapon_slot_unlock_levels."""

    @pytest.fixture
    def player(self):
        from src.entities.player import Player
        return Player(100, 100)

    def test_slots_unlock_as_player_levels(self, player):
        from src.entities.player_stats import unlocked_weapon_slots
        player.stats.gain_xp(1_000_000)  # разом до max_level
        expected = unlocked_weapon_slots(player.level)
        assert expected > 2  # хотя бы один уровень разлочки пройден
        assert len(player.weapons) == expected


# --- Патроны (v0.4.0b) -------------------------------------------------------

class TestAmmo:
    """PlayerCombat: магазин/резерв, гейтинг try_attack, reload, add_ammo."""

    @pytest.fixture
    def player(self):
        from src.entities.player import Player
        p = Player(100, 100)
        # На слот 0 (по умолчанию sword) сажаем rifle, чтобы тестировать
        # атаку без переключения слотов.
        p._combat.weapons[0] = create_weapon("rifle")
        # try_attack() гейтится cooldown'ом от pygame.time.get_ticks() -
        # без этого тест может флакать, если суммарное время с pygame.init()
        # ещё меньше cooldown_ms оружия (быстрый прогон файла).
        p._combat.last_attack_time = -1_000_000
        return p

    def test_starts_with_full_magazine(self, player):
        assert player.magazine_count() == RangedWeapon.magazine_size
        assert player.magazine_count() > 0

    def test_starts_with_configured_reserve(self, player):
        assert player.reserve_count() > 0

    def test_try_attack_consumes_one_bullet(self, player):
        start = player.magazine_count()
        player.try_attack()
        assert player.attacking is True
        assert player.magazine_count() == start - 1

    def test_try_attack_blocked_on_empty_magazine(self, player):
        player._combat.magazine["bullets"] = 0
        attack_id_before = player.attack_id
        player.try_attack()
        assert player.attacking is False
        assert player.attack_id == attack_id_before  # атака не взведена вовсе

    def test_attack_id_stable_across_frames_while_attacking(self, player):
        """Регресс на 'один снаряд на выстрел, не один на кадр': пока
        attacking=True, повторные try_attack() (как при зажатом Space
        несколько кадров) НЕ должны продвигать attack_id дальше - именно
        на этой стабильности держится edge-detection в game.py."""
        player.try_attack()
        attack_id_after_first = player.attack_id
        magazine_after_first = player.magazine_count()
        for _ in range(10):
            player.try_attack()
        assert player.attack_id == attack_id_after_first
        assert player.magazine_count() == magazine_after_first  # патрон не тратится повторно

    def test_melee_weapon_unaffected_by_empty_magazine(self, player):
        # Слот 1 - meele (spear по умолчанию из starting_slot_assignment)
        player.switch_weapon(1)
        player._combat.magazine["bullets"] = 0  # пустой магазин у rifle - неважно
        player.try_attack()
        assert player.attacking is True  # меч не расходует патроны

    def test_reload_moves_reserve_to_magazine(self, player):
        player._combat.magazine["bullets"] = 0
        reserve_before = player.reserve_count()
        ok = player.reload()
        assert ok is True
        assert player.magazine_count() == min(RangedWeapon.magazine_size, reserve_before)
        assert player.reserve_count() == reserve_before - player.magazine_count()

    def test_reload_caps_at_magazine_size(self, player):
        player._combat.reserve["bullets"] = 1000
        player.reload()
        assert player.magazine_count() == RangedWeapon.magazine_size

    def test_reload_noop_when_magazine_full(self, player):
        reserve_before = player.reserve_count()
        ok = player.reload()  # магазин уже полон при старте
        assert ok is False
        assert player.reserve_count() == reserve_before

    def test_reload_noop_when_reserve_empty(self, player):
        player._combat.magazine["bullets"] = 0
        player._combat.reserve["bullets"] = 0
        ok = player.reload()
        assert ok is False
        assert player.magazine_count() == 0

    def test_reload_blocked_during_attack(self, player):
        player._combat.magazine["bullets"] = 0
        player.attacking = True
        ok = player.reload()
        assert ok is False

    def test_add_ammo_caps_reserve(self, player):
        player.add_ammo("bullets", 1000, cap=90)
        assert player.reserve_count() == 90

    def test_melee_weapon_has_no_ammo_readout(self, player):
        player.switch_weapon(1)  # spear
        assert player.magazine_count() == 0
        assert player.reserve_count() == 0

