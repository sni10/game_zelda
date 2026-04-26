"""
Tests for v0.3.2 manual save slots in SaveSystem.

Покрывают:
- Round-trip: save_to_slot -> load_from_slot возвращает те же данные.
- list_manual_saves: пустой список / частично заполненный / правильный sort.
- Лимит 10 слотов (save_to_slot вне диапазона = False).
- delete_slot: удаление, повторное удаление = False.
- get_quicksave_metadata / get_free_slot.
- _read_metadata: повреждённый файл → valid=False, без падения.
- Quicksave и manual-слоты физически разделены (saves/quicksave.json
  vs saves/manual/slot_NN.json).
"""
import os
import json
import shutil
import tempfile

import pytest
import pygame

from src.systems.save_system import SaveSystem
from src.entities.player import Player
from src.world.world import World
from src.systems.pickup_manager import PickupManager
from src.core.game_stats import GameStats


@pytest.fixture(autouse=True, scope="module")
def _pygame_init():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


@pytest.fixture()
def save_system(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return SaveSystem()


@pytest.fixture()
def world():
    # Грузим реальный main_world.txt, чтобы EnemyManager был валиден.
    return World(map_file=os.path.join("F:/HOME/game_zelda/data", "main_world.txt"))


@pytest.fixture()
def player():
    return Player(100, 200)


# --- Базовый round-trip --------------------------------------------------

def test_save_to_slot_creates_file_in_manual_subdir(save_system, player, world):
    ok = save_system.save_to_slot(1, player, world)
    assert ok is True
    expected = os.path.join("saves", "manual", "slot_01.json")
    assert os.path.exists(expected)
    # quicksave не должен быть создан
    assert not os.path.exists(os.path.join("saves", "quicksave.json"))


def test_load_from_slot_round_trip(save_system, player, world):
    player.x = 555
    player.y = 777
    player.health = 42
    save_system.save_to_slot(3, player, world)

    data = save_system.load_from_slot(3)
    assert data is not None
    assert data["player"]["x"] == 555
    assert data["player"]["y"] == 777
    assert data["player"]["health"] == 42


def test_load_from_empty_slot_returns_none(save_system):
    assert save_system.load_from_slot(7) is None


# --- Лимит ---------------------------------------------------------------

def test_save_to_slot_out_of_range_rejected(save_system, player, world):
    assert save_system.save_to_slot(0, player, world) is False
    assert save_system.save_to_slot(11, player, world) is False
    assert save_system.save_to_slot(-1, player, world) is False


def test_save_to_all_10_slots(save_system, player, world):
    for i in range(1, 11):
        assert save_system.save_to_slot(i, player, world) is True
    saves = save_system.list_manual_saves()
    assert len(saves) == 10
    assert [s["slot_id"] for s in saves] == list(range(1, 11))


# --- list_manual_saves ---------------------------------------------------

def test_list_manual_saves_empty(save_system):
    assert save_system.list_manual_saves() == []


def test_list_manual_saves_partial(save_system, player, world):
    save_system.save_to_slot(2, player, world)
    save_system.save_to_slot(5, player, world)
    save_system.save_to_slot(9, player, world)

    saves = save_system.list_manual_saves()
    slot_ids = [s["slot_id"] for s in saves]
    assert slot_ids == [2, 5, 9]
    for s in saves:
        assert s["valid"] is True
        assert "timestamp" in s
        assert "level" in s
        assert "play_time" in s
        assert "hp" in s
        assert "max_hp" in s
        assert s["filename"].startswith("slot_")


# --- delete_slot ---------------------------------------------------------

def test_delete_slot(save_system, player, world):
    save_system.save_to_slot(4, player, world)
    assert save_system.slot_exists(4) is True
    assert save_system.delete_slot(4) is True
    assert save_system.slot_exists(4) is False
    # Повторное удаление пустого слота = False
    assert save_system.delete_slot(4) is False


# --- get_free_slot / get_quicksave_metadata ------------------------------

def test_get_free_slot_returns_first_empty(save_system, player, world):
    assert save_system.get_free_slot() == 1
    save_system.save_to_slot(1, player, world)
    save_system.save_to_slot(2, player, world)
    assert save_system.get_free_slot() == 3


def test_get_free_slot_returns_none_when_full(save_system, player, world):
    for i in range(1, 11):
        save_system.save_to_slot(i, player, world)
    assert save_system.get_free_slot() is None


def test_get_quicksave_metadata_none_when_no_quicksave(save_system):
    assert save_system.get_quicksave_metadata() is None


def test_get_quicksave_metadata_after_save_game(save_system, player, world):
    save_system.save_game(player, world)
    meta = save_system.get_quicksave_metadata()
    assert meta is not None
    assert meta["valid"] is True
    assert meta["filename"] == "quicksave.json"


# --- Метаданные / повреждённые файлы -------------------------------------

def test_read_metadata_corrupt_file(save_system, tmp_path):
    bad = tmp_path / "broken.json"
    bad.write_text("{not json")
    meta = save_system._read_metadata(str(bad))
    assert meta["valid"] is False
    assert meta["level"] == 0


def test_list_manual_saves_includes_corrupt_with_valid_false(
    save_system, player, world
):
    save_system.save_to_slot(1, player, world)
    # Подменяем slot_02 на мусор
    bad_path = os.path.join("saves", "manual", "slot_02.json")
    with open(bad_path, "w", encoding="utf-8") as f:
        f.write("{garbage")
    saves = save_system.list_manual_saves()
    slots = {s["slot_id"]: s for s in saves}
    assert 1 in slots and slots[1]["valid"] is True
    assert 2 in slots and slots[2]["valid"] is False


# --- Полная сериализация: с pickups и game_stats -------------------------

def test_round_trip_with_full_state(save_system, player, world):
    pm = PickupManager()
    gs = GameStats()
    gs.enemies_killed = 7
    gs.distance_traveled = 1234.5

    ok = save_system.save_to_slot(
        6, player, world,
        game_stats=gs, pickup_manager=pm,
        enemy_manager=world.enemy_manager,
    )
    assert ok is True

    data = save_system.load_from_slot(6)
    assert data is not None
    assert "game_stats" in data and isinstance(data["game_stats"], dict)
    assert data["game_stats"]["enemies_killed"] == 7
    assert "pickups" in data and isinstance(data["pickups"], list)
    assert "enemies" in data
