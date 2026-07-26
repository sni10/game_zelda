"""
ProjectileManager - управление летящими снарядами (Projectile) в мире.

Обязанности:
- Хранение списка живых снарядов
- Обновление позиции каждого снаряда по кадрам
- Коллизии: препятствия (world.check_collision), границы мира,
  живые враги (world.enemy_manager.enemies)
- Удаление истёкших/попавших снарядов

В отличие от мгновенных attack_rects (melee/AoE), снаряд - одноразовый
объект: попал/истёк -> удаляется. Дедуп через attack_id (как в
EnemyManager.apply_player_attack) не нужен - снаряд физически не может
ударить дважды.
"""
from typing import List, Dict
import math

import pygame

from src.core.config_loader import get_config
from src.entities.projectile import Projectile


class ProjectileManager:
    """Контейнер летящих снарядов для одного мира."""

    def __init__(self, world):
        self.world = world
        self.projectiles: List[Projectile] = []

    def spawn(self, projectile: Projectile) -> None:
        self.projectiles.append(projectile)

    def update(self, dt: float) -> List[Dict]:
        """Продвинуть все снаряды, применить коллизии.

        Возвращает список событий попадания вида {"killed": bool, "damage": int}
        - вызывающий код (game.py) решает что с ними делать (game_stats).
        """
        events: List[Dict] = []
        if not self.projectiles:
            return events

        kb_speed = get_config('COMBAT_ENEMY_KNOCKBACK_SPEED', 180)
        kb_dur = get_config('COMBAT_ENEMY_KNOCKBACK_DURATION', 0.12)

        for proj in self.projectiles:
            if proj.expired:
                continue

            proj.update(dt)
            if proj.expired:
                continue

            # Границы мира
            if not (0 <= proj.x <= self.world.width and 0 <= proj.y <= self.world.height):
                proj.expired = True
                continue

            # Препятствия - снаряд гасится об стену
            if self.world.check_collision(proj.rect):
                proj.expired = True
                continue

            # Живые враги - первое попадание гасит снаряд (без пробивания)
            for enemy in self.world.enemy_manager.enemies:
                if enemy.is_dead():
                    continue
                if proj.rect.colliderect(enemy.rect):
                    enemy.take_damage(proj.damage)
                    dx, dy = proj.dx, proj.dy
                    dist = math.hypot(dx, dy)
                    if dist < 1:
                        dx, dy, dist = 0, -1, 1
                    enemy.knockback_vx = (dx / dist) * kb_speed
                    enemy.knockback_vy = (dy / dist) * kb_speed
                    enemy.knockback_timer = kb_dur
                    events.append({"killed": enemy.is_dead(), "damage": proj.damage})
                    proj.expired = True
                    break

        self.projectiles = [p for p in self.projectiles if not p.expired]
        return events

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for proj in self.projectiles:
            proj.draw(screen, camera_x, camera_y)
