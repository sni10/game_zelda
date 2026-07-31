"""
Projectile - летящий снаряд (реальная баллистика для стрелкового оружия).

Single Responsibility: хранить позицию/направление/скорость и обновлять их
по кадрам. НЕ занимается коллизиями/уроном - это делает ProjectileManager
(симметрично тому, как Weapon не занимается коллизиями, а EnemyManager их
применяет к attack_rects).
"""
import math

import pygame


class Projectile:
    """Один летящий снаряд."""

    SIZE = 6  # визуальный размер круга, px (радиус отрисовки = SIZE // 2)
    # Хитбокс на 5% больше визуала - чуть более прощающие попадания без
    # изменения того, что видит игрок. ceil, иначе 6*1.05=6.3 обратно
    # округлится в 6 на пиксельной сетке pygame.Rect и увеличение исчезнет.
    HITBOX_SIZE = math.ceil(SIZE * 1.05)

    def __init__(self, x: float, y: float, dx: float, dy: float,
                 speed: float, damage: int, max_range: float,
                 color=(255, 220, 120)):
        self.x = x
        self.y = y
        self.dx = dx  # юнит-вектор направления (см. weapons.DIRECTION_VECTORS)
        self.dy = dy
        self.speed = speed
        self.damage = damage
        self.max_range = max_range
        self.color = color

        self.traveled = 0.0
        self.expired = False
        self.rect = pygame.Rect(
            int(x - self.HITBOX_SIZE / 2), int(y - self.HITBOX_SIZE / 2),
            self.HITBOX_SIZE, self.HITBOX_SIZE
        )

    def update(self, dt: float) -> None:
        """Продвинуть снаряд вдоль направления. Помечает expired при
        достижении максимальной дальности."""
        if self.expired:
            return
        step = self.speed * dt
        self.x += self.dx * step
        self.y += self.dy * step
        self.traveled += step
        self.rect.x = int(self.x - self.HITBOX_SIZE / 2)
        self.rect.y = int(self.y - self.HITBOX_SIZE / 2)
        if self.traveled >= self.max_range:
            self.expired = True

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        pygame.draw.circle(screen, self.color, (sx, sy), self.SIZE // 2)
