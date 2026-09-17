from types import SimpleNamespace

import pytest

from src.systems.mission import (
    Campaign,
    DefeatBossObjective,
    Mission,
    build_dev_campaign,
)


class MutableStats:
    def __init__(self, **values):
        self.values = values

    def to_dict(self):
        return dict(self.values)


def make_mission(name):
    return Mission(
        map_file=name,
        world_width=320,
        world_height=320,
        title=name,
        objective=DefeatBossObjective(),
    )


@pytest.mark.parametrize(
    ("boss_alive", "complete", "progress"),
    [
        (True, False, "Цель: уничтожить босса"),
        (False, True, "Босс повержен"),
    ],
)
def test_defeat_boss_objective(boss_alive, complete, progress):
    manager = SimpleNamespace(boss_alive=lambda: boss_alive)
    world = SimpleNamespace(enemy_manager=manager)
    objective = DefeatBossObjective()

    assert objective.is_complete(world) is complete
    assert objective.progress(world) == progress


def test_campaign_tracks_mission_delta_and_total():
    campaign = Campaign([make_mission("first"), make_mission("second")])
    stats = MutableStats(
        enemies_killed=2,
        damage_dealt=10,
        distance_traveled=5.0,
    )

    campaign.begin_mission(stats)
    stats.values.update(
        enemies_killed=5,
        damage_dealt=34,
        distance_traveled=12.5,
    )
    first = campaign.complete_mission(stats)

    assert first["enemies_killed"] == 3
    assert first["damage_dealt"] == 24
    assert first["distance_traveled"] == pytest.approx(7.5)

    assert campaign.advance() is campaign.current
    assert campaign.index == 1
    assert campaign.is_last is True

    campaign.begin_mission(stats)
    stats.values.update(enemies_killed=7, damage_dealt=40)
    second = campaign.complete_mission(stats)

    assert second["enemies_killed"] == 2
    assert campaign.total_snapshot()["enemies_killed"] == 5
    assert campaign.total_snapshot()["damage_dealt"] == 30


def test_campaign_cannot_advance_past_final_mission():
    campaign = Campaign([make_mission("only")])

    assert campaign.is_last is True
    assert campaign.advance() is None
    assert campaign.index == 0


def test_campaign_without_baseline_uses_zero_values():
    campaign = Campaign([make_mission("only")])
    stats = MutableStats(enemies_killed=4)

    snapshot = campaign.complete_mission(stats)

    assert snapshot["enemies_killed"] == 4
    assert snapshot["damage_dealt"] == 0


def test_build_dev_campaign_defines_two_ordered_missions():
    campaign = build_dev_campaign()

    assert [mission.map_file for mission in campaign.missions] == [
        "main_world",
        "big_world",
    ]
    assert all(
        isinstance(mission.objective, DefeatBossObjective)
        for mission in campaign.missions
    )
