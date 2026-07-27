"""
Тесты для InventoryScreen (v0.4.x): drag-and-drop слотов оружия мышью,
закрытие по Esc. Тестируем только логику handle_input (через синтетические
pygame-события), не draw().
"""
import os

import pytest
import pygame

from src.core.config_loader import load_config
from src.entities.player import Player
from src.ui.inventory_screen import InventoryScreen


@pytest.fixture(autouse=True, scope="module")
def _pygame_init():
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((800, 600))
    load_config()
    yield
    pygame.quit()


@pytest.fixture()
def player():
    p = Player(0, 0)
    p.unlock_slot()  # 3 слота: sword, spear, sword - удобно для drag-тестов
    return p


@pytest.fixture()
def screen_ui():
    return InventoryScreen()


def _key(k):
    return pygame.event.Event(pygame.KEYDOWN, {"key": k})


def _mouse_down(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button})


def _mouse_up(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": button})


# --- Esc -------------------------------------------------------------------

def test_escape_returns_close_action(screen_ui, player):
    action = screen_ui.handle_input(_key(pygame.K_ESCAPE), player)
    assert action == {"type": "close"}


def test_escape_clears_in_progress_drag(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    assert screen_ui._dragging_index == 0
    screen_ui.handle_input(_key(pygame.K_ESCAPE), player)
    assert screen_ui._dragging_index is None


# --- Drag-and-drop -----------------------------------------------------------

def test_drag_and_drop_swaps_slots(screen_ui, player):
    rects = screen_ui._slot_rects(player)

    down_action = screen_ui.handle_input(_mouse_down(rects[0].center), player)
    assert down_action is None
    assert screen_ui._dragging_index == 0

    up_action = screen_ui.handle_input(_mouse_up(rects[2].center), player)
    assert up_action == {"type": "move_weapon", "from_index": 0, "to_index": 2}
    assert screen_ui._dragging_index is None  # сброшен после drop


def test_drop_on_same_slot_is_noop(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up(rects[0].center), player)
    assert action is None
    assert screen_ui._dragging_index is None


def test_drop_outside_any_slot_cancels(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up((0, 0)), player)  # заведомо мимо слотов
    assert action is None
    assert screen_ui._dragging_index is None


def test_mouse_down_outside_slots_does_not_start_drag(screen_ui, player):
    action = screen_ui.handle_input(_mouse_down((0, 0)), player)
    assert action is None
    assert screen_ui._dragging_index is None


def test_mouse_up_without_prior_down_is_noop(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    action = screen_ui.handle_input(_mouse_up(rects[1].center), player)
    assert action is None


def test_right_click_ignored(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    action = screen_ui.handle_input(_mouse_down(rects[0].center, button=3), player)
    assert action is None
    assert screen_ui._dragging_index is None


# --- Геометрия ---------------------------------------------------------------

def test_slot_rects_count_matches_weapon_count(screen_ui, player):
    assert len(screen_ui._slot_rects(player)) == len(player.weapons) == 3


def test_slot_rects_do_not_overlap(screen_ui, player):
    rects = screen_ui._slot_rects(player)
    for i in range(len(rects) - 1):
        assert not rects[i].colliderect(rects[i + 1]) or rects[i].right <= rects[i + 1].left


# --- draw() smoke ------------------------------------------------------------

def test_draw_does_not_crash(screen_ui, player):
    screen = pygame.display.get_surface()
    screen_ui.draw(screen, player)  # без drag
    rects = screen_ui._slot_rects(player)
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    screen_ui.draw(screen, player)  # с активным drag (иконка следует за курсором)
