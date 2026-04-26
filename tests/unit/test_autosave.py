"""
Tests for v0.3.3 autosaves in SaveSystem.

Покрывают:
- Round-trip: autosave → load_from_autosave возвращает те же данные.
- Папка saves/autosave/ создаётся, файл называется autosave_NN.json.
- list_autosaves возвращает свежие сверху (по mtime).
- get_latest_autosave_metadata.
- Ротация: при limit=2 после 3-го autosave самый старый затирается.
- delete_autosave: удаление + повторное удаление = False.
- _enforce_autosave_limit: уменьшение лимита удаляет хвост.
- autosave_reason пропагандируется в metadata.reason.
- has_saves() в MainMenu учитывает saves/autosave/.
"""
import os
import time

import pytest
import pygame

from src.systems.save_system import SaveSystem
from src.entities.player import Player
from src.world.world import World


@pytest.fixture(autouse=True, scope="module")
def _pygame_init():
    # NB: не вызываем pygame.quit() в teardown — глобальный шрифт в
    # src/utils/debug.py кэшируется и без него тесты test_debug_coverage,
    # которые идут после, падают с SDL access violation.
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield


@pytest.fixture()
def save_system(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return SaveSystem()


@pytest.fixture()
def world():
    return World(map_file=os.path.join("F:/HOME/game_zelda/data", "main_world.txt"))


@pytest.fixture()
def player():
    return Player(100, 200)


# --- Базовый round-trip --------------------------------------------------

def test_autosave_creates_file_in_autosave_subdir(save_system, player, world):
    ok = save_system.autosave(player, world, reason="periodic", limit=3)
    assert ok is True
    expected = os.path.join("saves", "autosave", "autosave_01.json")
    assert os.path.exists(expected)
    # quicksave не создан
    assert not os.path.exists(os.path.join("saves", "quicksave.json"))


def test_autosave_round_trip(save_system, player, world):
    player.x = 321
    player.y = 654
    player.health = 17
    save_system.autosave(player, world, reason="level_up")
    data = save_system.load_from_autosave(1)
    assert data is not None
    assert data["player"]["x"] == 321
    assert data["player"]["y"] == 654
    assert data["player"]["health"] == 17
    assert data["autosave_reason"] == "level_up"


def test_load_from_empty_autosave_returns_none(save_system):
    assert save_system.load_from_autosave(2) is None


# --- list_autosaves / metadata ------------------------------------------

def test_list_autosaves_empty(save_system):
    assert save_system.list_autosaves() == []


def test_list_autosaves_sorted_newest_first(save_system, player, world):
    save_system.autosave(player, world, reason="periodic", limit=3)
    time.sleep(0.05)  # гарантируем разный mtime
    save_system.autosave(player, world, reason="level_up", limit=3)
    time.sleep(0.05)
    save_system.autosave(player, world, reason="periodic", limit=3)

    items = save_system.list_autosaves()
    assert len(items) == 3
    # Свежие сверху
    mtimes = [i["mtime"] for i in items]
    assert mtimes == sorted(mtimes, reverse=True)
    # reason проброшен в metadata
    assert items[0]["reason"] in ("periodic", "level_up")


def test_get_latest_autosave_metadata(save_system, player, world):
    assert save_system.get_latest_autosave_metadata() is None
    save_system.autosave(player, world, reason="manual")
    meta = save_system.get_latest_autosave_metadata()
    assert meta is not None
    assert meta["reason"] == "manual"
    assert meta["valid"] is True


# --- Ротация -------------------------------------------------------------

def test_autosave_rotation_overwrites_oldest(save_system, player, world):
    # Заполняем 2 слота при limit=2
    save_system.autosave(player, world, reason="periodic", limit=2)
    time.sleep(0.05)
    save_system.autosave(player, world, reason="periodic", limit=2)

    # Третий autosave должен затереть самый старый (slot_01)
    old_mtime_1 = os.path.getmtime(
        os.path.join("saves", "autosave", "autosave_01.json")
    )
    time.sleep(0.05)
    save_system.autosave(player, world, reason="level_up", limit=2)

    items = save_system.list_autosaves()
    # Всё ещё ровно 2 файла
    assert len(items) == 2
    # slot_01 был самым старым → теперь обновлён
    new_mtime_1 = os.path.getmtime(
        os.path.join("saves", "autosave", "autosave_01.json")
    )
    assert new_mtime_1 > old_mtime_1
    # И именно у него теперь reason=level_up
    slot_1_meta = next(i for i in items if i["slot_id"] == 1)
    assert slot_1_meta["reason"] == "level_up"


def test_autosave_enforce_limit_removes_tail(save_system, player, world):
    # Сначала пишем 3 автосейва
    save_system.autosave(player, world, limit=3)
    save_system.autosave(player, world, limit=3)
    save_system.autosave(player, world, limit=3)
    assert len(save_system.list_autosaves()) == 3

    # Лимит уменьшили до 2 — следующий autosave должен подчистить slot_03
    save_system.autosave(player, world, limit=2)
    items = save_system.list_autosaves()
    slot_ids = sorted(i["slot_id"] for i in items)
    assert slot_ids == [1, 2]
    assert not os.path.exists(
        os.path.join("saves", "autosave", "autosave_03.json")
    )


# --- delete_autosave -----------------------------------------------------

def test_delete_autosave(save_system, player, world):
    save_system.autosave(player, world)
    assert os.path.exists(
        os.path.join("saves", "autosave", "autosave_01.json")
    )
    assert save_system.delete_autosave(1) is True
    assert not os.path.exists(
        os.path.join("saves", "autosave", "autosave_01.json")
    )
    # Повторное удаление = False
    assert save_system.delete_autosave(1) is False


# --- has_saves в MainMenu ------------------------------------------------

def test_main_menu_has_saves_picks_autosave_only(tmp_path, monkeypatch,
                                                 save_system, player, world):
    # save_system fixture уже сделал chdir в tmp_path
    save_system.autosave(player, world)

    # Импортируем MainMenu лениво (нужен pygame.font)
    from src.ui.menu import MainMenu
    menu = MainMenu()
    assert menu.has_saves() is True
    # Quicksave не должен влиять — его нет
    assert menu.has_quicksave() is False


def test_invalid_limit_falls_back_to_default(save_system, player, world):
    # Передаём невалидное значение — функция не должна падать
    ok = save_system.autosave(player, world, limit="abc")
    assert ok is True
    items = save_system.list_autosaves()
    assert len(items) == 1
