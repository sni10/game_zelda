"""
PlayerCombat - боевые механики игрока.

Single Responsibility: управлять атакой (старт, таймер, cooldown, attack_id),
переключение оружий, расчёт зон поражения. Не знает про рендер или мир.
"""
import pygame

from src.entities.weapons import Weapon, default_loadout
from typing import List


class PlayerCombat:
    """Система атаки и оружия игрока."""

    def __init__(self):
        # Runtime-состояние текущей атаки
        self.attacking = False
        self.attack_timer = 0
        self.last_attack_time = 0
        # Уникальный ID взмаха: EnemyManager сравнивает его с last_hit_attack_id
        # у каждого врага, чтобы 1 атака = 1 урон (атака длится несколько кадров).
        self.attack_id = 0

        # Инвентарь оружий
        self.weapons: List[Weapon] = default_loadout()
        self.current_weapon_index = 0

    @property
    def current_weapon(self) -> Weapon:
        """Текущее активное оружие."""
        return self.weapons[self.current_weapon_index]

    def switch_weapon(self, index: int) -> bool:
        """Переключить оружие по индексу. Возвращает True если произошло."""
        if self.attacking:
            return False
        if 0 <= index < len(self.weapons) and index != self.current_weapon_index:
            self.current_weapon_index = index
            return True
        return False

    def try_attack(self) -> None:
        """Попытка атаки с учётом cooldown текущего оружия."""
        current_time = pygame.time.get_ticks()
        weapon = self.current_weapon
        if not self.attacking and current_time - self.last_attack_time > weapon.cooldown_ms:
            self.attacking = True
            self.attack_timer = current_time
            self.last_attack_time = current_time
            self.attack_id += 1

    def update_attack(self) -> None:
        """Обновить таймер атаки — вызывать каждый кадр."""
        if self.attacking:
            current_time = pygame.time.get_ticks()
            if current_time - self.attack_timer > self.current_weapon.duration_ms:
                self.attacking = False

    def get_attack_rects(self, player_rect: pygame.Rect, facing_direction: str) -> list:
        """Получить зоны поражения текущей атаки."""
        if not self.attacking:
            return []
        return self.current_weapon.get_attack_rects(player_rect, facing_direction)

