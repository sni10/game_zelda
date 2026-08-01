"""
Тесты системы оружий.

Покрывают:
- Симметричность зон поражения по 8 направлениям (фикс старого бага,
  где down/right были впритык, а up/left имели зазор).
- Параметризацию reach для разных типов оружия.
- RangedWeapon (Rifle) - реальная баллистика через Projectile, не мгновенный rect.
- Переключение оружий в Player.switch_weapon().
"""
import math
import os
import pytest
import pygame

from src.entities.weapons import (
    MeleeWeapon, PolearmWeapon, RangedWeapon, AoeWeapon,
    BurstRifle, ShotgunWeapon,
    DIRECTION_VECTORS, _rect_in_direction, _rect_in_vector_direction,
    pellet_directions,
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


class TestVectorDirection:
    """_rect_in_vector_direction - произвольный угол (360° прицеливание),
    не только 8 фиксированных направлений. _rect_in_direction (8-way) теперь
    тонкая обёртка над этой функцией - её поведение уже покрыто TestSymmetry
    и не меняется."""

    def test_matches_named_direction_for_canonical_vectors(self, player_rect):
        """На канонических 8 векторах результат идентичен старой функции."""
        for name, (dx, dy) in DIRECTION_VECTORS.items():
            expected = _rect_in_direction(player_rect, name, 16, 32, 32)
            actual = _rect_in_vector_direction(player_rect, dx, dy, 16, 32, 32)
            assert actual == expected

    def test_arbitrary_angle_returns_valid_rect(self, player_rect):
        """Угол, не кратный 45° (37°) - всё ещё валидный rect."""
        angle = math.radians(37)
        dx, dy = math.cos(angle), math.sin(angle)
        rect = _rect_in_vector_direction(player_rect, dx, dy, 16, 32, 32)
        assert isinstance(rect, pygame.Rect)
        assert rect.width == 32 and rect.height == 32

    def test_arbitrary_angle_is_further_from_center_than_reach_zero(self, player_rect):
        """При том же угле больший reach даёт зону дальше от игрока."""
        angle = math.radians(37)
        dx, dy = math.cos(angle), math.sin(angle)
        near = _rect_in_vector_direction(player_rect, dx, dy, 0, 32, 32)
        far = _rect_in_vector_direction(player_rect, dx, dy, 40, 32, 32)
        cx, cy = player_rect.center
        dist_near = math.hypot(near.centerx - cx, near.centery - cy)
        dist_far = math.hypot(far.centerx - cx, far.centery - cy)
        assert dist_far > dist_near

    def test_opposite_angles_are_mirrored(self, player_rect):
        """Произвольный угол и его противоположность (180°) зеркальны
        относительно центра игрока - та же симметрия, что и для 8-way."""
        angle = math.radians(37)
        dx, dy = math.cos(angle), math.sin(angle)
        a = _rect_in_vector_direction(player_rect, dx, dy, 16, 32, 32)
        b = _rect_in_vector_direction(player_rect, -dx, -dy, 16, 32, 32)
        cx, cy = player_rect.center
        assert (a.centerx - cx) == pytest.approx(-(b.centerx - cx), abs=1)
        assert (a.centery - cy) == pytest.approx(-(b.centery - cy), abs=1)


# --- Поведение конкретных оружий -------------------------------------------

class TestMeleeWeapon:
    """Меч: впритык, reach=0."""

    def test_no_gap(self, player_rect):
        sword = MeleeWeapon()
        assert sword.reach == 0
        rect = sword.get_attack_rects(player_rect, *DIRECTION_VECTORS['right'])[0]
        # Зона начинается ровно на правом ребре игрока
        assert rect.left == player_rect.right

    def test_returns_single_rect(self, player_rect):
        rects = MeleeWeapon().get_attack_rects(player_rect, *DIRECTION_VECTORS['up'])
        assert len(rects) == 1


class TestPolearmWeapon:
    """Копьё: с отступом полклетки."""

    def test_half_tile_gap(self, player_rect):
        spear = PolearmWeapon()
        assert spear.reach == 16
        rect = spear.get_attack_rects(player_rect, *DIRECTION_VECTORS['right'])[0]
        gap = rect.left - player_rect.right
        assert gap == 16


class TestRangedWeapon:
    """Rifle: реальная баллистика (Projectile), не мгновенный rect."""

    def test_no_instant_attack_rects(self, player_rect):
        """Урон наносит Projectile, get_attack_rects() пуст (иначе
        Player.draw() рисовал бы поверх летящей пули старую рамку)."""
        rifle = RangedWeapon()
        assert rifle.get_attack_rects(player_rect, *DIRECTION_VECTORS['right']) == []

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

    def test_unlimited_range(self):
        """Скорострельное оружие (Rifle) - дистанцию не ограничиваем: пуля
        летит, пока не упрётся в стену/границу мира, не по таймеру дальности."""
        assert RangedWeapon.projectile_max_range == float('inf')


class TestBurstRifle:
    """SMG: одно нажатие даёт очередь из 3 пуль (burst_count), но списывает
    ровно 1 патрон из магазина - как и одиночный Rifle (см. TestAmmo в
    test_combat_loop.py / PlayerCombat.try_attack). Мгновенных attack_rects
    нет (как и у Rifle - урон наносит Projectile, не rect)."""

    def test_no_instant_attack_rects(self, player_rect):
        smg = BurstRifle()
        assert smg.get_attack_rects(player_rect, *DIRECTION_VECTORS['right']) == []

    def test_burst_params(self):
        assert BurstRifle.fires_projectile is True
        assert BurstRifle.burst_count == 3
        assert BurstRifle.burst_delay_ms > 0

    def test_unlimited_range(self):
        """Скорострельное оружие - дистанция не ограничена (см. RangedWeapon)."""
        assert BurstRifle.projectile_max_range == float('inf')

    def test_duration_covers_full_burst(self):
        """attacking должен держаться дольше, чем время до последнего
        выстрела очереди - иначе последний выстрел никогда не заспавнится
        (см. Game.update() burst-таймер в game.py)."""
        last_shot_at = (BurstRifle.burst_count - 1) * BurstRifle.burst_delay_ms
        assert BurstRifle.duration_ms > last_shot_at


class TestShotgunWeapon:
    """Дробовик: 5 пуль веером, мгновенных attack_rects тоже нет."""

    def test_no_instant_attack_rects(self, player_rect):
        shotgun = ShotgunWeapon()
        assert shotgun.get_attack_rects(player_rect, *DIRECTION_VECTORS['right']) == []

    def test_pellet_params(self):
        assert ShotgunWeapon.fires_projectile is True
        assert ShotgunWeapon.pellet_count == 5
        assert ShotgunWeapon.spread_angle_deg > 0
        assert ShotgunWeapon.burst_count == 1  # весь веер - один выстрел, не очередь

    def test_limited_but_extended_range(self):
        """Дробовик - единственное оружие с ограничением дальности (не
        скорострельное), но оно увеличено на 10-15% относительно старого
        дефолта Rifle (420px)."""
        assert 420 * 1.10 <= ShotgunWeapon.projectile_max_range <= 420 * 1.15


class TestPelletDirections:
    """weapons.pellet_directions - веер снарядов для Shotgun (pure function,
    без зависимости от Game/Player - см. Game._spawn_projectile)."""

    def test_single_pellet_returns_aim_direction_unchanged(self):
        dirs = pellet_directions(1.0, 0.0, pellet_count=1, spread_angle_deg=30)
        assert dirs == [(1.0, 0.0)]

    def test_returns_pellet_count_directions(self):
        dirs = pellet_directions(1.0, 0.0, pellet_count=5, spread_angle_deg=30)
        assert len(dirs) == 5

    def test_middle_pellet_is_exact_aim_direction(self):
        """Нечётный pellet_count (5) - средняя пулька точно по центральной
        оси прицела, как просил пользователь ("по центральной оси")."""
        dirs = pellet_directions(0.0, 1.0, pellet_count=5, spread_angle_deg=30)
        middle = dirs[2]
        assert middle[0] == pytest.approx(0.0, abs=1e-9)
        assert middle[1] == pytest.approx(1.0, abs=1e-9)

    def test_outer_pellets_are_symmetric_around_aim(self):
        dirs = pellet_directions(0.0, 1.0, pellet_count=5, spread_angle_deg=30)
        first, last = dirs[0], dirs[-1]
        # Симметричны относительно оси прицела (dy одинаковый, dx зеркальный)
        assert first[0] == pytest.approx(-last[0])
        assert first[1] == pytest.approx(last[1])

    def test_all_directions_are_unit_vectors(self):
        dirs = pellet_directions(1.0, 0.0, pellet_count=5, spread_angle_deg=45)
        for dx, dy in dirs:
            assert math.hypot(dx, dy) == pytest.approx(1.0)

    def test_zero_spread_collapses_all_pellets_to_aim(self):
        dirs = pellet_directions(1.0, 0.0, pellet_count=5, spread_angle_deg=0)
        for dx, dy in dirs:
            assert dx == pytest.approx(1.0)
            assert dy == pytest.approx(0.0, abs=1e-9)


class TestAoeWeapon:
    """Бомба: одна большая зона 3x3 клетки."""

    def test_large_area(self, player_rect):
        bomb = AoeWeapon()
        rect = bomb.get_attack_rects(player_rect, *DIRECTION_VECTORS['right'])[0]
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
        assert set(WEAPON_CATALOG) == {
            "sword", "spear", "rifle", "smg", "shotgun", "bomb",
        }

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
    """PlayerCombat.unlock_slot / set_slot_weapon (см. player_combat.py)."""

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

    def test_set_slot_weapon_assigns_given_weapon(self, player):
        assert player.weapons[0].weapon_id == "sword"
        assert player.set_slot_weapon(0, "rifle") is True
        assert player.weapons[0].weapon_id == "rifle"

    def test_set_slot_weapon_any_catalog_id_works(self, player):
        for weapon_id in WEAPON_CATALOG:
            assert player.set_slot_weapon(0, weapon_id) is True
            assert player.weapons[0].weapon_id == weapon_id

    def test_set_slot_weapon_unknown_id_rejected(self, player):
        assert player.set_slot_weapon(0, "does-not-exist") is False
        assert player.weapons[0].weapon_id == "sword"  # не изменилось

    def test_set_slot_weapon_blocked_during_attack(self, player):
        player.attacking = True
        assert player.set_slot_weapon(0, "rifle") is False

    def test_set_slot_weapon_out_of_range_rejected(self, player):
        assert player.set_slot_weapon(5, "rifle") is False  # слот ещё не разлочен

    def test_switch_to_locked_slot_rejected(self, player):
        # Только 2 слота есть - индекс 2 ещё не существует
        assert player.switch_weapon(2) is False


class TestMoveWeapon:
    """PlayerCombat.move_weapon - своп двух слотов (drag-and-drop в InventoryScreen)."""

    @pytest.fixture
    def player(self):
        from src.entities.player import Player
        p = Player(100, 100)
        p.unlock_slot()
        p.unlock_slot()
        return p  # 4 слота: sword, spear, sword, sword

    def test_swaps_two_slots(self, player):
        before = [w.weapon_id for w in player.weapons]
        assert player.move_weapon(0, 1) is True
        after = [w.weapon_id for w in player.weapons]
        assert after[0] == before[1]
        assert after[1] == before[0]
        # Остальные слоты не тронуты
        assert after[2:] == before[2:]

    def test_same_index_is_noop(self, player):
        before = [w.weapon_id for w in player.weapons]
        assert player.move_weapon(1, 1) is False
        assert [w.weapon_id for w in player.weapons] == before

    def test_out_of_range_index_rejected(self, player):
        assert player.move_weapon(0, 99) is False
        assert player.move_weapon(99, 0) is False

    def test_blocked_during_attack(self, player):
        player.attacking = True
        before = [w.weapon_id for w in player.weapons]
        assert player.move_weapon(0, 1) is False
        assert [w.weapon_id for w in player.weapons] == before

    def test_current_weapon_index_not_adjusted_by_swap(self, player):
        # current_weapon_index указывает на позицию, не на объект - после
        # свопа активным становится то, что физически лежит в этом слоте.
        player.current_weapon_index = 0
        assert player.current_weapon.weapon_id == "sword"
        player.move_weapon(0, 1)
        assert player.current_weapon_index == 0
        assert player.current_weapon.weapon_id == "spear"


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

