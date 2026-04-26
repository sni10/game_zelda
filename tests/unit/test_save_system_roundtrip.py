"""
Round-trip тесты для SaveSystem (issue v0.3.1 — фикс F9).

Проверяем что save -> load -> apply восстанавливает:
- weapon_index, iframe_timer, прогрессию игрока,
- живых врагов (тип/HP/позиция),
- лежащие пикапы (тип/позиция/lifetime),
- GameStats (kills/distance/playtime),
- валидацию схемы (повреждённый JSON не должен крашить).
"""
import os
import json
import tempfile
import shutil

import pygame
import pytest

# Headless pygame
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from src.core.config_loader import load_config
from src.core.game_stats import GameStats
from src.entities.player import Player
from src.entities.pickup import HeartPickup, CoinPickup, XPOrbPickup
from src.systems.pickup_manager import PickupManager
from src.systems.enemy_manager import EnemyManager
from src.systems.save_system import SaveSystem


@pytest.fixture(scope="module", autouse=True)
def _pygame_init():
    pygame.init()
    load_config()
    yield
    pygame.quit()


@pytest.fixture
def tmp_save_system():
    tmpdir = tempfile.mkdtemp()
    ss = SaveSystem()
    ss.saves_dir = tmpdir
    yield ss
    shutil.rmtree(tmpdir, ignore_errors=True)


class _MockWorld:
    """Минимальный мир для EnemyManager.serialize/deserialize.

    EnemyManager при desearialize только создаёт patrol_zone из x/y и
    не вызывает collision-проверки (только в spawn_enemy). Поэтому
    width/height достаточно.
    """
    def __init__(self, w=2000, h=2000):
        self.width = w
        self.height = h
        self.enemy_manager = None  # будет назначен снаружи

    def check_collision(self, rect):
        return False


# ---------------------------------------------------------------------------
# Player round-trip
# ---------------------------------------------------------------------------

def test_player_roundtrip_full(tmp_save_system):
    """Сохранение/загрузка игрока: позиция, HP, прогрессия, оружие, iframe."""
    world = _MockWorld()
    p = Player(123.0, 456.0)
    p.health = 7
    p.max_health = 12
    p.facing_direction = "up_left"
    p.stats.level = 4
    p.stats.xp = 33
    p.stats.coins = 99
    p.stats.damage_bonus = 2
    p.stats.iframe_timer = 0.42
    p.current_weapon_index = 2  # bow

    assert tmp_save_system.save_game(p, world) is True
    data = tmp_save_system.load_game()
    assert data is not None

    p2 = Player(0, 0)
    tmp_save_system.apply_save_data_to_player(p2, data)

    assert p2.x == 123.0
    assert p2.y == 456.0
    assert p2.health == 7
    assert p2.max_health == 12
    assert p2.facing_direction == "up_left"
    assert p2.stats.level == 4
    assert p2.stats.xp == 33
    assert p2.stats.coins == 99
    assert p2.stats.damage_bonus == 2
    assert p2.stats.iframe_timer == pytest.approx(0.42)
    assert p2.current_weapon_index == 2


# ---------------------------------------------------------------------------
# Pickups round-trip
# ---------------------------------------------------------------------------

def test_pickups_roundtrip(tmp_save_system):
    pm = PickupManager()
    pm.spawn(HeartPickup(100.0, 200.0))
    pm.spawn(CoinPickup(150.5, 250.5))
    pm.spawn(XPOrbPickup(300.0, 400.0))
    # Эмулируем что сердце "повисело" 5 секунд
    pm.pickups[0].lifetime = pm.pickups[0].lifetime - 5.0

    p = Player(0, 0)
    world = _MockWorld()

    assert tmp_save_system.save_game(p, world, pickup_manager=pm) is True
    data = tmp_save_system.load_game()
    assert data is not None
    assert isinstance(data.get("pickups"), list)
    assert len(data["pickups"]) == 3

    pm2 = PickupManager()
    tmp_save_system.apply_save_data_to_pickups(pm2, data)

    assert pm2.count() == 3
    types = sorted(type(x).__name__ for x in pm2.pickups)
    assert types == ["CoinPickup", "HeartPickup", "XPOrbPickup"]
    # Lifetime восстановлен
    heart = next(x for x in pm2.pickups if isinstance(x, HeartPickup))
    assert heart.lifetime == pytest.approx(pm.pickups[0].lifetime)
    # Позиции восстановлены
    coin = next(x for x in pm2.pickups if isinstance(x, CoinPickup))
    assert (coin.x, coin.y) == (150.5, 250.5)


# ---------------------------------------------------------------------------
# Enemies round-trip
# ---------------------------------------------------------------------------

def test_enemies_roundtrip(tmp_save_system):
    world = _MockWorld()
    em = EnemyManager(world)
    world.enemy_manager = em

    spawned = em.spawn_initial(player_x=-9999, player_y=-9999)
    assert spawned > 0, "тест-предусловие: должны заспавниться враги"

    # Раним первого врага и взводим его cooldown
    first = em.enemies[0]
    first.health = max(1, first.stats.max_health - 1)
    first.attack_cooldown_timer = 0.7

    snapshot_count = len(em.enemies)
    snapshot_first = (
        first.stats.name.lower(), first.x, first.y,
        first.health, first.attack_cooldown_timer,
    )

    p = Player(0, 0)
    assert tmp_save_system.save_game(p, world, enemy_manager=em) is True
    data = tmp_save_system.load_game()
    assert data is not None

    # Чистый менеджер
    world2 = _MockWorld()
    em2 = EnemyManager(world2)
    world2.enemy_manager = em2

    tmp_save_system.apply_save_data_to_enemies(em2, data)

    assert len(em2.enemies) == snapshot_count
    e0 = em2.enemies[0]
    assert e0.stats.name.lower() == snapshot_first[0]
    assert e0.x == snapshot_first[1]
    assert e0.y == snapshot_first[2]
    assert e0.health == snapshot_first[3]
    assert e0.attack_cooldown_timer == pytest.approx(snapshot_first[4])
    # target_counts тоже сохранены — авто-респавн продолжит работать
    assert em2.target_counts == em.target_counts


# ---------------------------------------------------------------------------
# GameStats round-trip
# ---------------------------------------------------------------------------

def test_game_stats_roundtrip(tmp_save_system):
    gs = GameStats()
    gs.enemies_killed = 17
    gs.damage_dealt = 120
    gs.damage_taken = 33
    gs.attacks_made = 50
    gs.items_collected = 4
    gs.distance_traveled = 1234.5
    gs.deaths = 1
    gs.health_lost = 33
    gs.health_recovered = 10
    gs.last_x = 500
    gs.last_y = 600
    # Эмулируем что мы наиграли минуту
    import time
    gs.start_time = time.time() - 60.0

    p = Player(0, 0)
    world = _MockWorld()

    assert tmp_save_system.save_game(p, world, game_stats=gs) is True
    data = tmp_save_system.load_game()
    assert data is not None

    gs2 = GameStats()
    tmp_save_system.apply_save_data_to_game_stats(gs2, data)

    assert gs2.enemies_killed == 17
    assert gs2.damage_dealt == 120
    assert gs2.damage_taken == 33
    assert gs2.attacks_made == 50
    assert gs2.items_collected == 4
    assert gs2.distance_traveled == pytest.approx(1234.5)
    assert gs2.deaths == 1
    assert gs2.health_lost == 33
    assert gs2.health_recovered == 10
    assert gs2.last_x == 500
    assert gs2.last_y == 600
    # play_time восстановлен (>= 60 секунд, с учётом микро-дрейфа)
    gs2.update_play_time()
    assert gs2.play_time >= 60.0


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_load_invalid_json_returns_none(tmp_save_system):
    bad_path = os.path.join(tmp_save_system.saves_dir, "bad.json")
    with open(bad_path, "w", encoding="utf-8") as f:
        f.write("{ not valid json")
    assert tmp_save_system.load_game("bad.json") is None


def test_load_missing_player_returns_none(tmp_save_system):
    bad_path = os.path.join(tmp_save_system.saves_dir, "noplayer.json")
    with open(bad_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1.1"}, f)
    assert tmp_save_system.load_game("noplayer.json") is None


def test_load_player_wrong_types_returns_none(tmp_save_system):
    bad_path = os.path.join(tmp_save_system.saves_dir, "wrong.json")
    with open(bad_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.1",
            "player": {"x": "not-a-number", "y": 0, "health": 10, "max_health": 10},
        }, f)
    assert tmp_save_system.load_game("wrong.json") is None


def test_load_legacy_v1_0_still_works(tmp_save_system):
    """Старый сейв без enemies/pickups/game_stats всё ещё открывается."""
    legacy_path = os.path.join(tmp_save_system.saves_dir, "legacy.json")
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0",
            "timestamp": "2026-04-26T12:00:00Z",
            "player": {
                "x": 100, "y": 200,
                "health": 5, "max_health": 10,
                "facing_direction": "down",
                "level": 2, "xp": 5, "coins": 10, "damage_bonus": 0,
            },
            "world": {"current_map": "main_world"},
        }, f)
    data = tmp_save_system.load_game("legacy.json")
    assert data is not None

    p = Player(0, 0)
    tmp_save_system.apply_save_data_to_player(p, data)
    assert p.x == 100
    assert p.health == 5
    assert p.stats.level == 2
