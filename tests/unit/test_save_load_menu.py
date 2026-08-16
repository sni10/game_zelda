"""
Tests for v0.3.2 SaveLoadMenu UI logic.

Тестируем только логику handle_input/refresh без вызовов draw, чтобы
не зависеть от фактического экрана.
"""
import os

import pytest
import pygame

from src.core.config_loader import get_config
from src.systems.save_system import SaveSystem
from src.ui.save_load_menu import SaveLoadMenu
from src.entities.player import Player
from src.world.world import World


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
    return World(map_file=os.path.join(
        "F:/HOME/game_zelda/data", "main_world.txt"))


@pytest.fixture()
def player():
    return Player(0, 0)


def _key(k):
    e = pygame.event.Event(pygame.KEYDOWN, {"key": k})
    return e


def _motion(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos})


def _click(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button})


# --- LOAD mode ----------------------------------------------------------

def test_load_mode_empty(save_system):
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    assert menu.entries == []
    # Esc → back
    assert menu.handle_input(_key(pygame.K_ESCAPE)) == {"type": "back"}
    # Enter без entries → ничего
    assert menu.handle_input(_key(pygame.K_RETURN)) is None


def test_load_mode_lists_quicksave_and_slots(save_system, player, world):
    save_system.save_game(player, world)            # quicksave
    save_system.save_to_slot(2, player, world)
    save_system.save_to_slot(5, player, world)

    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    kinds = [e["kind"] for e in menu.entries]
    assert kinds == ["quicksave", "manual", "manual"]
    assert menu.entries[1]["slot_id"] == 2
    assert menu.entries[2]["slot_id"] == 5


def test_load_mode_enter_quicksave(save_system, player, world):
    save_system.save_game(player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    # Курсор на quicksave (первая строка)
    action = menu.handle_input(_key(pygame.K_RETURN))
    assert action == {"type": "load_quicksave"}


def test_load_mode_enter_slot(save_system, player, world):
    save_system.save_to_slot(3, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    action = menu.handle_input(_key(pygame.K_RETURN))
    assert action == {"type": "load_slot", "slot_id": 3}


def test_load_mode_navigation(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    save_system.save_to_slot(2, player, world)
    save_system.save_to_slot(3, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    assert menu.selected_index == 0
    menu.handle_input(_key(pygame.K_DOWN))
    assert menu.selected_index == 1
    menu.handle_input(_key(pygame.K_DOWN))
    assert menu.selected_index == 2
    # wrap
    menu.handle_input(_key(pygame.K_DOWN))
    assert menu.selected_index == 0
    menu.handle_input(_key(pygame.K_UP))
    assert menu.selected_index == 2


# --- SAVE mode ----------------------------------------------------------

def test_save_mode_shows_all_10_slots(save_system):
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    assert len(menu.entries) == 10
    assert all(e["kind"] == "manual" for e in menu.entries)
    assert all(e["meta"] is None for e in menu.entries)


def test_save_mode_enter_empty_slot_no_modal(save_system):
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    action = menu.handle_input(_key(pygame.K_RETURN))
    assert action == {"type": "save_slot", "slot_id": 1}
    assert menu.modal is None


def test_save_mode_enter_filled_slot_opens_overwrite_modal(
    save_system, player, world
):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    # курсор на slot_01 — он теперь занят
    action = menu.handle_input(_key(pygame.K_RETURN))
    assert action is None
    assert menu.modal == "overwrite"
    assert menu.modal_slot_id == 1

    # N отменяет модалку
    menu.handle_input(_key(pygame.K_n))
    assert menu.modal is None

    # Y подтверждает
    menu.handle_input(_key(pygame.K_RETURN))  # снова открыть модалку
    assert menu.modal == "overwrite"
    action = menu.handle_input(_key(pygame.K_y))
    assert action == {"type": "save_slot", "slot_id": 1}
    assert menu.modal is None


def test_save_mode_delete_filled_slot_modal_then_confirm(
    save_system, player, world
):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    # курсор на slot_01 (заполнен)
    action = menu.handle_input(_key(pygame.K_DELETE))
    assert action is None
    assert menu.modal == "delete"

    action = menu.handle_input(_key(pygame.K_y))
    assert action == {"type": "delete_slot", "slot_id": 1}


def test_save_mode_delete_empty_slot_does_nothing(save_system):
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    action = menu.handle_input(_key(pygame.K_DELETE))
    assert action is None
    assert menu.modal is None


def test_load_mode_delete_quicksave_blocked(save_system, player, world):
    save_system.save_game(player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    # курсор на quicksave
    action = menu.handle_input(_key(pygame.K_DELETE))
    assert action is None
    assert menu.modal is None  # quicksave удалить нельзя


def test_load_mode_delete_manual_slot(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    # курсор на manual-слоте (единственная строка)
    action = menu.handle_input(_key(pygame.K_DELETE))
    assert action is None
    assert menu.modal == "delete"
    action = menu.handle_input(_key(pygame.K_y))
    assert action == {"type": "delete_slot", "slot_id": 1}


def test_set_mode_resets_state(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    menu.selected_index = 0
    menu.set_mode(SaveLoadMenu.MODE_SAVE)
    assert menu.mode == SaveLoadMenu.MODE_SAVE
    assert menu.selected_index == 0
    assert menu.modal is None
    assert len(menu.entries) == 10


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        SaveLoadMenu(SaveSystem(), mode="bogus")


# --- Autosave entries (v0.3.3) ------------------------------------------

def test_load_mode_lists_autosaves_after_quicksave(save_system, player, world):
    """Автосейвы попадают в LOAD-меню между quicksave и manual-слотами."""
    save_system.save_game(player, world)               # quicksave
    save_system.autosave(player, world, reason="periodic")
    save_system.autosave(player, world, reason="level_up")
    save_system.save_to_slot(1, player, world)

    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    kinds = [e["kind"] for e in menu.entries]
    # quicksave первым, потом autosaves, потом manual
    assert kinds[0] == "quicksave"
    assert kinds[-1] == "manual"
    assert kinds.count("autosave") == 2


def test_load_mode_enter_autosave(save_system, player, world):
    save_system.autosave(player, world, reason="periodic")
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    # курсор на единственной строке = autosave
    action = menu.handle_input(_key(pygame.K_RETURN))
    assert action["type"] == "load_autosave"
    assert action["slot_id"] >= 1


def test_load_mode_delete_autosave_via_modal(save_system, player, world):
    save_system.autosave(player, world, reason="periodic")
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    action = menu.handle_input(_key(pygame.K_DELETE))
    assert action is None
    assert menu.modal == "delete"
    assert menu.modal_kind == "autosave"
    action = menu.handle_input(_key(pygame.K_y))
    assert action["type"] == "delete_autosave"


# --- Mouse control --------------------------------------------------------

def test_click_on_row_selects_without_activating(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    save_system.save_to_slot(2, player, world)
    save_system.save_to_slot(3, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    assert menu.selected_index == 0

    _, rect = menu._entry_rects()[2]
    action = menu.handle_input(_click(rect.center))
    assert action is None
    assert menu.selected_index == 2


def test_click_outside_rows_and_buttons_does_nothing(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    action = menu.handle_input(_click((1, 1)))
    assert action is None
    assert menu.selected_index == 0


def test_hover_updates_visual_state_only(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    save_system.save_to_slot(2, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    _, rect = menu._entry_rects()[1]
    action = menu.handle_input(_motion(rect.center))
    assert action is None
    assert menu.selected_index == 0  # hover не двигает курсор выбора
    assert menu._hover_kind == "entry"
    assert menu._hover_index == 1


def test_primary_button_click_loads_quicksave(save_system, player, world):
    save_system.save_game(player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    name, _label, rect = [b for b in menu._action_buttons()
                           if b[0] == "primary"][0]
    action = menu.handle_input(_click(rect.center))
    assert action == {"type": "load_quicksave"}


def test_delete_button_click_opens_modal_then_yes_button_confirms(
    save_system, player, world
):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    _, _, delete_rect = [b for b in menu._action_buttons()
                         if b[0] == "delete"][0]
    action = menu.handle_input(_click(delete_rect.center))
    assert action is None
    assert menu.modal == "delete"

    yes_rect = menu._modal_button_rects(
        get_config('WIDTH'), get_config('HEIGHT')
    )["yes"]
    action = menu.handle_input(_click(yes_rect.center))
    assert action == {"type": "delete_slot", "slot_id": 1}
    assert menu.modal is None


def test_modal_no_button_cancels(save_system, player, world):
    save_system.save_to_slot(1, player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_SAVE)
    menu.handle_input(_key(pygame.K_RETURN))  # открыть overwrite-модалку
    assert menu.modal == "overwrite"

    no_rect = menu._modal_button_rects(
        get_config('WIDTH'), get_config('HEIGHT')
    )["no"]
    action = menu.handle_input(_click(no_rect.center))
    assert action is None
    assert menu.modal is None


def test_back_button_click_returns_back_action(save_system):
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    _, _, back_rect = [b for b in menu._action_buttons()
                       if b[0] == "back"][0]
    action = menu.handle_input(_click(back_rect.center))
    assert action == {"type": "back"}


def test_delete_button_click_noop_on_quicksave(save_system, player, world):
    save_system.save_game(player, world)
    menu = SaveLoadMenu(save_system, mode=SaveLoadMenu.MODE_LOAD)
    # курсор на quicksave — удаление недоступно
    _, _, delete_rect = [b for b in menu._action_buttons()
                         if b[0] == "delete"][0]
    action = menu.handle_input(_click(delete_rect.center))
    assert action is None
    assert menu.modal is None
