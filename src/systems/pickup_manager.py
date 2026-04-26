"""
PickupManager — спавн, обновление и рендер всех пикапов в мире.
"""
from typing import List
import pygame

from src.entities.pickup import Pickup, HeartPickup, CoinPickup, XPOrbPickup


# Регистр (type_id -> класс) для сериализации/десериализации.
# При добавлении нового типа пикапа достаточно зарегистрировать его здесь.
_PICKUP_TYPES = {
    "heart": HeartPickup,
    "coin": CoinPickup,
    "xp_orb": XPOrbPickup,
}
_PICKUP_TYPE_IDS = {cls: tid for tid, cls in _PICKUP_TYPES.items()}


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

    # --- Сериализация ------------------------------------------------------

    def serialize(self) -> list:
        """Сохранить лежащие на земле пикапы."""
        out = []
        for p in self.pickups:
            tid = _PICKUP_TYPE_IDS.get(type(p))
            if tid is None:
                continue  # неизвестный тип — пропускаем
            out.append({
                "type": tid,
                "x": float(p.x),
                "y": float(p.y),
                "lifetime": float(p.lifetime),
            })
        return out

    def deserialize(self, data: list) -> None:
        """Восстановить пикапы из списка (заменяет текущие)."""
        self.pickups = []
        if not data:
            return
        for item in data:
            tid = item.get("type")
            cls = _PICKUP_TYPES.get(tid)
            if cls is None:
                continue
            p = cls(float(item.get("x", 0)), float(item.get("y", 0)))
            if "lifetime" in item:
                p.lifetime = float(item["lifetime"])
            self.pickups.append(p)

