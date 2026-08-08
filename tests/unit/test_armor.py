"""
Тесты системы брони (issue #63).

Покрывают:
- Armor: базовые статы, reset_shield.
- EquipmentSlots: equip/total_* агрегаты, распределение урона по щиту
  (absorb_damage) - равномерное, с переливом на живые предметы, полный
  пробой в остаток.
- create_armor()/default_equipment() - чтение статов из config.ini.
"""

import os

import pygame
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.core.config_loader import load_config
from src.entities.armor import (
    Armor,
    EquipmentSlots,
    SLOT_NAMES,
    ARMOR_CATALOG,
    create_armor,
    default_equipment,
)


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    # Не вызываем pygame.quit() в teardown - другие тестовые модули держат
    # синглтон-хэндлы (например src/utils/debug.py: font создаётся один раз
    # на уровне модуля), quit() их инвалидирует и роняет полный прогон
    # тестов access violation при следующем использовании.
    pygame.init()
    load_config()
    yield


def _armor(slot="helmet", max_shield=100, defense=0, speed_mod=0.0, hp_bonus=0):
    a = Armor(
        max_shield=max_shield, defense=defense, speed_mod=speed_mod, hp_bonus=hp_bonus
    )
    a.slot = slot
    return a


# --- Armor -------------------------------------------------------------


class TestArmor:
    def test_starts_at_full_shield(self):
        a = _armor(max_shield=250)
        assert a.current_shield == 250

    def test_reset_shield_restores_full(self):
        a = _armor(max_shield=250)
        a.current_shield = 10
        a.reset_shield()
        assert a.current_shield == 250


# --- EquipmentSlots aggregates -------------------------------------------


class TestEquipmentSlotsAggregates:
    def test_empty_slots_have_zero_totals(self):
        eq = EquipmentSlots()
        assert eq.total_max_shield == 0
        assert eq.total_shield == 0
        assert eq.total_defense == 0
        assert eq.total_speed_mod == 0.0
        assert eq.total_hp_bonus == 0

    def test_equip_fills_named_slot(self):
        eq = EquipmentSlots()
        helmet = _armor(slot="helmet", max_shield=500)
        eq.equip(helmet)
        assert eq.slots["helmet"] is helmet
        assert all(eq.slots[s] is None for s in SLOT_NAMES if s != "helmet")

    def test_equip_same_slot_replaces_previous(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=100))
        eq.equip(_armor(slot="helmet", max_shield=200))
        assert eq.slots["helmet"].max_shield == 200

    def test_totals_sum_across_equipped_pieces(self):
        eq = EquipmentSlots()
        eq.equip(
            _armor(slot="helmet", max_shield=500, defense=1, speed_mod=0.1, hp_bonus=5)
        )
        eq.equip(
            _armor(
                slot="chest", max_shield=500, defense=2, speed_mod=-0.05, hp_bonus=10
            )
        )
        assert eq.total_max_shield == 1000
        assert eq.total_shield == 1000
        assert eq.total_defense == 3
        assert eq.total_speed_mod == pytest.approx(0.05)
        assert eq.total_hp_bonus == 15


# --- absorb_damage distribution ------------------------------------------


class TestAbsorbDamageDistribution:
    def test_zero_damage_is_noop(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=100))
        overflow = eq.absorb_damage(0)
        assert overflow == 0
        assert eq.total_shield == 100

    def test_no_equipped_armor_passes_all_damage_through(self):
        eq = EquipmentSlots()
        assert eq.absorb_damage(50) == 50

    def test_evenly_split_between_two_pieces(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=100))
        eq.equip(_armor(slot="chest", max_shield=100))
        overflow = eq.absorb_damage(60)
        assert overflow == 0
        assert eq.slots["helmet"].current_shield == 70
        assert eq.slots["chest"].current_shield == 70

    def test_uneven_split_distributes_remainder(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=100))
        eq.equip(_armor(slot="chest", max_shield=100))
        eq.equip(_armor(slot="arms", max_shield=100))
        overflow = eq.absorb_damage(10)  # 10 / 3 -> 4,3,3
        assert overflow == 0
        shields = sorted(a.current_shield for a in eq._equipped())
        assert shields == [96, 97, 97]
        assert sum(shields) == 300 - 10

    def test_depleted_piece_overflow_goes_to_remaining_pieces(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=10))
        eq.equip(_armor(slot="chest", max_shield=100))
        overflow = eq.absorb_damage(60)  # 30/30 split, helmet only has 10
        assert overflow == 0
        assert eq.slots["helmet"].current_shield == 0
        # helmet absorbed 10, remaining 20 all go to chest (30 initial + 20 spillover)
        assert eq.slots["chest"].current_shield == 100 - 50

    def test_damage_exceeding_total_shield_returns_overflow_for_hp(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=10))
        eq.equip(_armor(slot="chest", max_shield=10))
        overflow = eq.absorb_damage(50)
        assert eq.total_shield == 0
        assert overflow == 30

    def test_broken_piece_untouched_by_further_damage(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=10))
        eq.absorb_damage(10)  # deplete helmet while it's the only piece equipped
        assert eq.slots["helmet"].current_shield == 0

        eq.equip(_armor(slot="chest", max_shield=100))
        overflow = eq.absorb_damage(5)
        assert overflow == 0
        assert eq.slots["helmet"].current_shield == 0
        assert eq.slots["chest"].current_shield == 95

    def test_reset_all_shields(self):
        eq = EquipmentSlots()
        eq.equip(_armor(slot="helmet", max_shield=100))
        eq.equip(_armor(slot="chest", max_shield=100))
        eq.absorb_damage(150)
        eq.reset_all_shields()
        assert eq.total_shield == eq.total_max_shield


# --- config-driven construction -------------------------------------------


class TestCreateArmorFromConfig:
    def test_catalog_has_all_four_slots(self):
        slots = {cls.slot for cls in ARMOR_CATALOG.values()}
        assert slots == set(SLOT_NAMES)

    def test_create_armor_reads_stats_from_config(self):
        helmet = create_armor("helmet_standard")
        assert helmet.max_shield == 500
        assert helmet.current_shield == 500
        assert helmet.slot == "helmet"

    def test_default_equipment_fills_all_slots(self):
        eq = default_equipment()
        assert all(eq.slots[s] is not None for s in SLOT_NAMES)
        assert eq.total_max_shield == 500 + 500 + 250 + 350
