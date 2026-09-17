import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(autouse=True)
def isolated_runtime():
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def main_world_path(project_root):
    return project_root / "data" / "main_world.txt"


@pytest.fixture
def save_root(tmp_path):
    return tmp_path / "saves"


@pytest.fixture
def log_root(tmp_path):
    return tmp_path / "logs"


@pytest.fixture
def deterministic_ticks(monkeypatch):
    current = {"value": 0}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: current["value"])

    def advance(milliseconds):
        current["value"] += milliseconds
        return current["value"]

    return advance


@pytest.fixture
def deterministic_mtime(monkeypatch):
    counter = iter(range(1_000_000, 2_000_000))

    def set_next(path):
        value = next(counter)
        os.utime(path, (value, value))
        return value

    return set_next
