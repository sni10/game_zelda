"""
PlayerStats - модель здоровья и характеристик игрока.

Single Responsibility: хранить HP, наносить/лечить урон, проверять смерть.
Не знает про pygame, ввод, рендер или мир.
"""


class PlayerStats:
    """Здоровье и базовые характеристики игрока."""

    def __init__(self, max_health: int):
        self.max_health = max_health
        self.health = max_health

    def is_dead(self) -> bool:
        return self.health <= 0

    def take_damage(self, damage: int, game_stats=None) -> None:
        """Нанести урон. Если game_stats передан — зафиксировать."""
        if self.is_dead():
            return
        self.health = max(0, self.health - damage)
        if game_stats:
            game_stats.record_damage_taken(damage)

    def heal(self, amount: int) -> None:
        """Восстановить здоровье (не выше max)."""
        if not self.is_dead():
            self.health = min(self.health + amount, self.max_health)

    def get_health_percentage(self) -> float:
        """Процент здоровья (0.0 – 1.0)."""
        return self.health / self.max_health if self.max_health > 0 else 0.0

