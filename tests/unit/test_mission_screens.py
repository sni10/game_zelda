import pygame
import pytest

from src.ui.map_transition import MapTransition
from src.ui.mission_screens import CampaignCompleteScreen, MissionCompleteScreen


@pytest.mark.parametrize(
    ("screen_type", "expected"),
    [(MissionCompleteScreen, "NEXT"), (CampaignCompleteScreen, "MENU")],
)
def test_stats_screens_accept_keyboard_and_button(screen_type, expected):
    args = (
        (800, 600, "Mission", {})
        if screen_type is MissionCompleteScreen
        else (800, 600, {})
    )
    screen = screen_type(*args)

    assert (
        screen.handle_input(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        == expected
    )
    assert (
        screen.handle_input(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=screen.button_rect.center
            )
        )
        == expected
    )
    assert (
        screen.handle_input(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))
        )
        is None
    )


def test_stats_screen_tracks_hover():
    screen = MissionCompleteScreen(800, 600, "Mission", {})

    screen.handle_input(
        pygame.event.Event(pygame.MOUSEMOTION, pos=screen.button_rect.center)
    )
    assert screen.button_hovered is True
    screen.handle_input(pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0)))
    assert screen.button_hovered is False


def test_map_transition_swaps_once_and_finishes_both_phases():
    calls = []
    transition = MapTransition()
    transition.start(lambda: calls.append("swap"))

    transition.update(0.5)
    assert calls == ["swap"]
    assert transition.active is True

    transition.update(0.5)
    assert calls == ["swap"]
    assert transition.active is False


def test_map_transition_handles_large_delta_once():
    calls = []
    transition = MapTransition()
    transition.start(lambda: calls.append("swap"))

    transition.update(1.5)

    assert calls == ["swap"]
    assert transition.active is False
