"""
Pickup — предметы, выпадающие из врагов.

3 типа:
- HeartPickup: восстанавливает HP
- CoinPickup: добавляет монеты
- XPOrbPickup: даёт XP

Каждый пикап рисуется простой геометрией (без спрайтов).
"""
import math
import pygame
from abc import ABC, abstractmethod
from src.core.config_loader import get_config


class Pickup(ABC):
    """Базовый класс пикапа."""

    SIZE = 12  # размер хитбокса

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(int(x), int(y), self.SIZE, self.SIZE)
        self.lifetime = get_config('PICKUPS_LIFETIME', 30.0)
        self.collected = False

    def update(self, dt: float, player) -> None:
        """Обновление: магнит + сбор + lifetime."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.collected = True
            return

        magnet_r = get_config('PICKUPS_MAGNET_RADIUS', 60)
        magnet_s = get_config('PICKUPS_MAGNET_SPEED', 260)

        dx = player.x + player.width / 2 - (self.x + self.SIZE / 2)
        dy = player.y + player.height / 2 - (self.y + self.SIZE / 2)
        dist = math.hypot(dx, dy)

        if dist < magnet_r and dist > 1:
            # Магнит — летим к игроку
            nx = dx / dist
            ny = dy / dist
            self.x += nx * magnet_s * dt
            self.y += ny * magnet_s * dt
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

        # Сбор по коллизии
        if self.rect.colliderect(player.rect):
            self.apply(player)
            self.collected = True

    @abstractmethod
    def apply(self, player) -> None:
        """Применить эффект пикапа к игроку."""
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        raise NotImplementedError

    @property
    def is_expired(self) -> bool:
        return self.collected


class HeartPickup(Pickup):
    """Восстанавливает HP."""

    def apply(self, player) -> None:
        amount = get_config('PICKUPS_HEART_HEAL_AMOUNT', 1)
        player.heal(amount)

    def draw(self, screen, camera_x, camera_y):
        sx = int(self.x - camera_x) + self.SIZE // 2
        sy = int(self.y - camera_y) + self.SIZE // 2
        # Красный кружок-сердечко
        pygame.draw.circle(screen, (255, 40, 40), (sx, sy), self.SIZE // 2)
        pygame.draw.circle(screen, (200, 0, 0), (sx, sy), self.SIZE // 2, 1)


class CoinPickup(Pickup):
    """Добавляет монету."""

    def apply(self, player) -> None:
        amount = get_config('PICKUPS_COIN_VALUE', 1)
        player.stats.add_coins(amount)

    def draw(self, screen, camera_x, camera_y):
        sx = int(self.x - camera_x) + self.SIZE // 2
        sy = int(self.y - camera_y) + self.SIZE // 2
        # Жёлтый ромб
        pts = [
            (sx, sy - self.SIZE // 2),
            (sx + self.SIZE // 2, sy),
            (sx, sy + self.SIZE // 2),
            (sx - self.SIZE // 2, sy),
        ]
        pygame.draw.polygon(screen, (255, 220, 50), pts)
        pygame.draw.polygon(screen, (180, 150, 0), pts, 1)


class XPOrbPickup(Pickup):
    """Даёт XP.

    amount - явное количество XP (например, с учётом бонуса ближнего боя
    в enemy_manager). Если не передано - берётся дефолт из конфига
    (обратная совместимость со старыми сейвами/вызовами).
    """

    def __init__(self, x: float, y: float, amount: int = None):
        super().__init__(x, y)
        self.amount = (
            amount if amount is not None else get_config('PICKUPS_XP_ORB_VALUE', 5)
        )

    def apply(self, player) -> None:
        player.stats.gain_xp(self.amount)

    def draw(self, screen, camera_x, camera_y):
        sx = int(self.x - camera_x) + self.SIZE // 2
        sy = int(self.y - camera_y) + self.SIZE // 2
        # Голубой шар
        pygame.draw.circle(screen, (80, 180, 255), (sx, sy), self.SIZE // 2)
        pygame.draw.circle(screen, (40, 120, 200), (sx, sy), self.SIZE // 2, 1)


class AmmoPickup(Pickup):
    """Патроны в резерв (см. PlayerCombat.add_ammo).

    ammo_type - какой тип патронов (сейчас только "bullets" для Rifle).
    amount - количество; влияет и на визуал (3 условных "размера" одного и
    того же пикапа, без буквенной вложенности ящик->обойма->патрон)."""

    def __init__(self, x: float, y: float, ammo_type: str = "bullets", amount: int = 10):
        super().__init__(x, y)
        self.ammo_type = ammo_type
        self.amount = amount

    def apply(self, player) -> None:
        cap = get_config('AMMO_RIFLE_RESERVE_CAP', 90)
        player.add_ammo(self.ammo_type, self.amount, cap)

    def draw(self, screen, camera_x, camera_y):
        sx = int(self.x - camera_x) + self.SIZE // 2
        sy = int(self.y - camera_y) + self.SIZE // 2
        if self.amount > 20:
            # Ящик - жёлто-коричневый квадрат
            size = self.SIZE
            rect = pygame.Rect(sx - size // 2, sy - size // 2, size, size)
            pygame.draw.rect(screen, (150, 110, 40), rect)
            pygame.draw.rect(screen, (90, 60, 20), rect, 1)
        elif self.amount > 8:
            # Обойма - серый прямоугольник
            w, h = self.SIZE, self.SIZE // 2
            rect = pygame.Rect(sx - w // 2, sy - h // 2, w, h)
            pygame.draw.rect(screen, (120, 120, 130), rect)
            pygame.draw.rect(screen, (60, 60, 70), rect, 1)
        else:
            # Патроны - мелкая латунная точка
            pygame.draw.circle(screen, (200, 170, 60), (sx, sy), self.SIZE // 3)

