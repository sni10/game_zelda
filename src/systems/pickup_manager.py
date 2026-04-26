"""
PickupManager — спавн, обновление и рендер всех пикапов в мире.
"""
from typing import List
import pygame

from src.entities.pickup import Pickup


class PickupManager:
    """Контейнер всех пикапов."""

    def __init__(self):
        self.pickups: List[Pickup] = []

    def spawn(self, pickup: Pickup) -> None:
        self.pickups.append(pickup)

    def update(self, dt: float, player) -> None:
        """Обновить все пикапы (магнит + сбор + expire)."""
        for p in self.pickups:
            p.update(dt, player)
        self.pickups = [p for p in self.pickups if not p.is_expired]

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for p in self.pickups:
            p.draw(screen, camera_x, camera_y)

    def count(self) -> int:
        return len(self.pickups)

