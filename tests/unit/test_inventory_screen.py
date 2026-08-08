"""
Тесты для InventoryScreen (v0.4.x): drag-and-drop между слотами, drag-and-drop
из каталога оружия в слот, locked-слоты (не разлоченные игроком) как
неинтерактивное превью, закрытие по Esc. Тестируем только логику
handle_input (через синтетические pygame-события), не draw().
"""
import os

import pytest
import pygame

from src.core.config_loader import load_config
from src.entities.player import Player
from src.entities.player_combat import MAX_WEAPON_SLOTS
from src.entities.weapons import WEAPON_CATALOG
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
    p.unlock_slot()  # 3 разлоченных слота: sword, spear, sword
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


# --- Esc/I/Tab ---------------------------------------------------------------

def test_escape_returns_close_action(screen_ui, player):
    action = screen_ui.handle_input(_key(pygame.K_ESCAPE), player)
    assert action == {"type": "close"}


def test_i_key_returns_close_action(screen_ui, player):
    """I - тот же toggle, что открыл инвентарь - должен и закрывать его."""
    action = screen_ui.handle_input(_key(pygame.K_i), player)
    assert action == {"type": "close"}


def test_tab_key_returns_close_action(screen_ui, player):
    """Tab - альтернативный toggle инвентаря наравне с I."""
    action = screen_ui.handle_input(_key(pygame.K_TAB), player)
    assert action == {"type": "close"}


def test_escape_clears_in_progress_drag(screen_ui, player):
    rects = screen_ui._slot_rects()
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    assert screen_ui._dragging == ("slot", 0)
    screen_ui.handle_input(_key(pygame.K_ESCAPE), player)
    assert screen_ui._dragging is None


# --- Drag-and-drop между слотами --------------------------------------------

def test_drag_and_drop_swaps_slots(screen_ui, player):
    rects = screen_ui._slot_rects()

    down_action = screen_ui.handle_input(_mouse_down(rects[0].center), player)
    assert down_action is None
    assert screen_ui._dragging == ("slot", 0)

    up_action = screen_ui.handle_input(_mouse_up(rects[2].center), player)
    assert up_action == {"type": "move_weapon", "from_index": 0, "to_index": 2}
    assert screen_ui._dragging is None  # сброшен после drop


def test_drop_on_same_slot_is_noop(screen_ui, player):
    rects = screen_ui._slot_rects()
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up(rects[0].center), player)
    assert action is None
    assert screen_ui._dragging is None


def test_drop_outside_any_slot_cancels(screen_ui, player):
    rects = screen_ui._slot_rects()
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up((0, 0)), player)  # заведомо мимо слотов
    assert action is None
    assert screen_ui._dragging is None


def test_mouse_down_outside_slots_and_catalog_does_not_start_drag(screen_ui, player):
    action = screen_ui.handle_input(_mouse_down((0, 0)), player)
    assert action is None
    assert screen_ui._dragging is None


def test_mouse_up_without_prior_down_is_noop(screen_ui, player):
    rects = screen_ui._slot_rects()
    action = screen_ui.handle_input(_mouse_up(rects[1].center), player)
    assert action is None


def test_right_click_ignored(screen_ui, player):
    rects = screen_ui._slot_rects()
    action = screen_ui.handle_input(_mouse_down(rects[0].center, button=3), player)
    assert action is None
    assert screen_ui._dragging is None


# --- Locked-слоты (ещё не разлоченные) --------------------------------------

def test_locked_slot_does_not_start_drag(screen_ui, player):
    """У player 3 разлоченных слота - слот с индексом 3 (4-й) ещё locked,
    из него нельзя тащить оружие."""
    rects = screen_ui._slot_rects()
    action = screen_ui.handle_input(_mouse_down(rects[3].center), player)
    assert action is None
    assert screen_ui._dragging is None


def test_cannot_drop_onto_locked_slot(screen_ui, player):
    """Перетаскивание слота 0 на locked-слот 3 не даёт действия."""
    rects = screen_ui._slot_rects()
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up(rects[3].center), player)
    assert action is None
    assert screen_ui._dragging is None


# --- Каталог оружия (замена убранному Tab) ----------------------------------

def test_drag_from_catalog_onto_slot_sets_weapon(screen_ui, player):
    catalog_rects = screen_ui._catalog_rects()
    rifle_index = list(WEAPON_CATALOG).index("rifle")

    down_action = screen_ui.handle_input(
        _mouse_down(catalog_rects[rifle_index].center), player
    )
    assert down_action is None
    assert screen_ui._dragging == ("catalog", "rifle")

    slot_rects = screen_ui._slot_rects()
    up_action = screen_ui.handle_input(_mouse_up(slot_rects[0].center), player)
    assert up_action == {"type": "set_slot_weapon", "index": 0, "weapon_id": "rifle"}
    assert screen_ui._dragging is None


def test_drag_from_catalog_onto_locked_slot_is_noop(screen_ui, player):
    catalog_rects = screen_ui._catalog_rects()
    screen_ui.handle_input(_mouse_down(catalog_rects[0].center), player)
    slot_rects = screen_ui._slot_rects()
    action = screen_ui.handle_input(_mouse_up(slot_rects[3].center), player)  # locked
    assert action is None


def test_drag_from_catalog_dropped_outside_cancels(screen_ui, player):
    catalog_rects = screen_ui._catalog_rects()
    screen_ui.handle_input(_mouse_down(catalog_rects[0].center), player)
    action = screen_ui.handle_input(_mouse_up((0, 0)), player)
    assert action is None
    assert screen_ui._dragging is None


def test_all_catalog_weapons_have_rects(screen_ui):
    assert len(screen_ui._catalog_rects()) == len(WEAPON_CATALOG)


# --- Геометрия ---------------------------------------------------------------

def test_slot_rects_always_show_max_slots(screen_ui, player):
    """Слотов всегда MAX_WEAPON_SLOTS (8), независимо от того, сколько
    игрок уже разлочил - недостающие рисуются locked (см. draw())."""
    assert len(screen_ui._slot_rects()) == MAX_WEAPON_SLOTS
    assert len(player.weapons) == 3  # разлочено меньше, чем всего слотов


def test_slot_rects_do_not_overlap(screen_ui):
    rects = screen_ui._slot_rects()
    for i in range(len(rects) - 1):
        assert not rects[i].colliderect(rects[i + 1]) or rects[i].right <= rects[i + 1].left


def test_catalog_rects_do_not_overlap(screen_ui):
    rects = screen_ui._catalog_rects()
    for i in range(len(rects) - 1):
        assert not rects[i].colliderect(rects[i + 1]) or rects[i].right <= rects[i + 1].left


# --- Броня (issue #63) -------------------------------------------------------

def test_armor_bar_rects_one_per_slot(screen_ui):
    from src.entities.armor import SLOT_NAMES
    rects = screen_ui._armor_bar_rects()
    assert len(rects) == len(SLOT_NAMES)


def test_armor_bar_rects_do_not_overlap(screen_ui):
    rects = screen_ui._armor_bar_rects()
    for i in range(len(rects) - 1):
        assert rects[i].right <= rects[i + 1].left


def test_draw_reflects_depleted_armor_shield(screen_ui, player):
    """После пробития щита brony draw() не крашится и current_shield=0."""
    screen = pygame.display.get_surface()
    player.equipment.absorb_damage(player.equipment.total_max_shield)
    assert player.equipment.total_shield == 0
    screen_ui.draw(screen, player)  # не должно крашнуться


# --- draw() smoke ------------------------------------------------------------

def test_draw_does_not_crash(screen_ui, player):
    screen = pygame.display.get_surface()
    screen_ui.draw(screen, player)  # без drag - в т.ч. locked-слоты и каталог
    rects = screen_ui._slot_rects()
    screen_ui.handle_input(_mouse_down(rects[0].center), player)
    screen_ui.draw(screen, player)  # с активным drag из слота

    catalog_rects = screen_ui._catalog_rects()
    screen_ui.handle_input(_key(pygame.K_ESCAPE), player)  # сброс предыдущего drag
    screen_ui.handle_input(_mouse_down(catalog_rects[0].center), player)
    screen_ui.draw(screen, player)  # с активным drag из каталога
