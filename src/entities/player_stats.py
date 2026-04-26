"""
тPlayerStats - модель здоровья, прогрессии и характеристик игрока.

Single Responsibility: хранить HP/XP/Level/Coins, наносить/лечить урон,
проверять смерть, управлять i-frames и level-up.
Не знает про pygame, ввод, рендер или мир.
"""
from src.core.config_loader import get_config


class PlayerStats:
    """Здоровье, прогрессия и базовые характеристики игрока."""

    def __init__(self, max_health: int):
        # HP
        self.max_health = max_health
        self.health = max_health

        # i-frames
        self.iframe_timer = 0.0
        self._iframe_duration = get_config('COMBAT_PLAYER_IFRAME_DURATION', 0.6)

        # Прогрессия
        self.level = 1
        self.xp = 0
        self.coins = 0
        self.damage_bonus = 0

        # Конфиг прогрессии (кеш)
        self._xp_base = get_config('PROGRESSION_XP_BASE', 20)
        self._xp_growth = get_config('PROGRESSION_XP_GROWTH', 1.5)
        self._hp_per_level = get_config('PROGRESSION_HP_PER_LEVEL', 1)
        self._damage_per_level = get_config('PROGRESSION_DAMAGE_PER_LEVEL', 0)
        self._heal_on_level_up = get_config('PROGRESSION_HEAL_ON_LEVEL_UP', True)
        self._max_level = get_config('PROGRESSION_MAX_LEVEL', 20)

    # --- HP -----------------------------------------------------------------

    def is_dead(self) -> bool:
        return self.health <= 0

    def take_damage(self, damage: int, game_stats=None, ignore_iframes: bool = False) -> bool:
        """Нанести урон. Уважает i-frames (кроме ignore_iframes=True).
        Возвращает True если урон прошёл."""
        if self.is_dead():
            return False
        if not ignore_iframes and self.iframe_timer > 0:
            return False
        self.health = max(0, self.health - damage)
        if not ignore_iframes:
            self.iframe_timer = self._iframe_duration
        if game_stats:
            game_stats.record_damage_taken(damage)
        return True

    def heal(self, amount: int) -> None:
        """Восстановить здоровье (не выше max)."""
        if not self.is_dead():
            self.health = min(self.health + amount, self.max_health)

    def get_health_percentage(self) -> float:
        """Процент здоровья (0.0 – 1.0)."""
        return self.health / self.max_health if self.max_health > 0 else 0.0

    def update(self, dt: float) -> None:
        """Тик таймеров (вызывать каждый кадр)."""
        if self.iframe_timer > 0:
            self.iframe_timer = max(0.0, self.iframe_timer - dt)

    @property
    def is_invulnerable(self) -> bool:
        return self.iframe_timer > 0

    # --- Прогрессия ---------------------------------------------------------

    @property
    def xp_to_next_level(self) -> int:
        """Сколько XP нужно до следующего уровня."""
        return xp_for_next_level(self.level, self._xp_base, self._xp_growth)

    def gain_xp(self, amount: int) -> int:
        """Добавить XP. Может вызвать несколько level-up за раз.
        Возвращает количество поднятых уровней."""
        if self.level >= self._max_level:
            return 0
        self.xp += amount
        levels_gained = 0
        while self.xp >= self.xp_to_next_level and self.level < self._max_level:
            self.xp -= self.xp_to_next_level
            self._level_up()
            levels_gained += 1
        # Кап — лишний XP не теряется, но level-up не происходит
        if self.level >= self._max_level:
            self.xp = 0
        return levels_gained

    def _level_up(self) -> None:
        self.level += 1
        self.max_health += self._hp_per_level
        self.damage_bonus += self._damage_per_level
        if self._heal_on_level_up:
            self.health = self.max_health

    def add_coins(self, amount: int) -> None:
        self.coins += amount


# --- Чистые функции прогрессии -------------------------------------------

def xp_for_next_level(level: int, xp_base: int = 20,
                      xp_growth: float = 1.5) -> int:
    """Формула XP до следующего уровня: base * (level ** growth)."""
    return int(xp_base * (level ** xp_growth))
