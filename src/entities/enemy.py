"""
Враги - базовый класс Enemy + 3 типа (Light/Heavy/Fast).
Архитектурные решения:
- Композиция > наследование: Enemy агрегирует EnemyStats и AIBehavior.
  Подклассы только меняют дефолты статов и стратегии. Это позволяет
  легко добавить десятки врагов без иерархии классов.
- Стат-данные читаются из config.ini через get_config() - баланс
  меняется без правки кода.
- Каждый враг имеет patrol_zone (pygame.Rect) - замкнутая область
  патрулирования. Поведение уважает зону.
"""
from dataclasses import dataclass
from typing import Tuple
import pygame
from src.core.config_loader import get_config
from src.entities.enemy_ai import AIBehavior, PatrolBehavior, ChaseBehavior
@dataclass
class EnemyStats:
    """Статы одного типа врага. Берутся из config.ini."""
    name: str
    max_health: int
    speed: float
    width: int
    height: int
    color: Tuple[int, int, int]
    damage: int  # урон игроку при будущем контактном бое
class Enemy:
    """Базовый враг с HP, AI и базовой отрисовкой."""
    def __init__(self, x, y, stats: EnemyStats, ai: AIBehavior,
                 patrol_zone: pygame.Rect):
        self.x = float(x)
        self.y = float(y)
        self.stats = stats
        self.ai = ai
        self.patrol_zone = patrol_zone
        self.health = stats.max_health
        self.rect = pygame.Rect(int(x), int(y), stats.width, stats.height)
        # Защита от множественного урона от одной атаки игрока.
        # Атаки длятся 200-400мс - без этого враг получал бы урон
        # каждый кадр, пока зона атаки на нём.
        self.last_hit_attack_id = 0
        # Время последнего попадания - для flash-эффекта
        self.last_hit_time = 0
        self.HIT_FLASH_DURATION_MS = 100
        # Knockback state
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0
        self.knockback_timer = 0.0
        # Attack cooldown — после удара враг не может бить N секунд
        self.attack_cooldown_timer = 0.0
    def take_damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)
        self.last_hit_time = pygame.time.get_ticks()
    def is_dead(self) -> bool:
        return self.health <= 0
    def update(self, dt: float, world, player=None) -> None:
        if self.is_dead():
            return
        # Тик attack cooldown
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer = max(0.0, self.attack_cooldown_timer - dt)
        # Запоминаем позицию до движения
        old_x, old_y = self.x, self.y
        # Knockback приоритетнее AI
        if self.knockback_timer > 0:
            self.knockback_timer -= dt
            new_x = self.x + self.knockback_vx * dt
            new_y = self.y + self.knockback_vy * dt
            import pygame as _pg
            candidate = _pg.Rect(int(new_x), int(new_y),
                                 self.rect.width, self.rect.height)
            blocked = (world is not None and world.check_collision(candidate))
            if not blocked and player is not None:
                blocked = candidate.colliderect(player.rect)
            if not blocked:
                self.x = new_x
                self.y = new_y
                self.rect.x = int(new_x)
                self.rect.y = int(new_y)
            if self.knockback_timer <= 0:
                self.knockback_vx = 0.0
                self.knockback_vy = 0.0
            return
        self.ai.update(self, dt, world, player)
        # После AI: не допускаем пересечения с хитбоксом игрока
        if player is not None and self.rect.colliderect(player.rect):
            self.x = old_x
            self.y = old_y
            self.rect.x = int(old_x)
            self.rect.y = int(old_y)
    def draw(self, screen, camera_x, camera_y) -> None:
        if self.is_dead():
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        # Frustum cull
        if (sx + self.stats.width < 0 or sy + self.stats.height < 0 or
                sx > screen.get_width() or sy > screen.get_height()):
            return
        # Flash при попадании
        now = pygame.time.get_ticks()
        if now - self.last_hit_time < self.HIT_FLASH_DURATION_MS:
            color = (255, 255, 255)
        else:
            color = self.stats.color
        pygame.draw.rect(screen, color,
                         (sx, sy, self.stats.width, self.stats.height))
        if self.health < self.stats.max_health:
            self._draw_health_bar(screen, sx, sy)
    def _draw_health_bar(self, screen, sx, sy) -> None:
        bar_w = self.stats.width
        bar_h = 4
        bar_y = sy - bar_h - 2
        pygame.draw.rect(screen, (40, 40, 40), (sx, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * self.health / self.stats.max_health)
        if fill_w > 0:
            pygame.draw.rect(screen, (60, 200, 60),
                             (sx, bar_y, fill_w, bar_h))
    def __repr__(self):
        return (f"{self.__class__.__name__}"
                f"(name={self.stats.name}, hp={self.health}/{self.stats.max_health}, "
                f"pos=({int(self.x)}, {int(self.y)}))")
def _stats_from_config(prefix: str, name: str) -> EnemyStats:
    """Прочитать EnemyStats из секции [enemies] config.ini."""
    return EnemyStats(
        name=name,
        max_health=get_config(f'ENEMIES_{prefix}_MAX_HEALTH'),
        speed=float(get_config(f'ENEMIES_{prefix}_SPEED')),
        width=get_config(f'ENEMIES_{prefix}_SIZE'),
        height=get_config(f'ENEMIES_{prefix}_SIZE'),
        color=get_config(f'ENEMIES_{prefix}_COLOR'),
        damage=get_config(f'ENEMIES_{prefix}_DAMAGE'),
    )
class LightEnemy(Enemy):
    """Лёгкий враг: малый, средний по скорости, 1 HP."""
    TYPE_ID = 'light'
    @classmethod
    def create(cls, x, y, patrol_zone) -> 'LightEnemy':
        return cls(x, y,
                   stats=_stats_from_config('LIGHT', 'Light'),
                   ai=PatrolBehavior(),
                   patrol_zone=patrol_zone)
class HeavyEnemy(Enemy):
    """Тяжёлый враг: большой, медленный, 3 HP."""
    TYPE_ID = 'heavy'
    @classmethod
    def create(cls, x, y, patrol_zone) -> 'HeavyEnemy':
        chase_r = get_config('ENEMIES_HEAVY_CHASE_RADIUS', 100)
        lose_r = get_config('ENEMIES_CHASE_LOSE_RADIUS', 280)
        ai = ChaseBehavior(chase_radius=chase_r, lose_radius=lose_r,
                           patrol_fallback=PatrolBehavior(repath_interval=3.0))
        return cls(x, y,
                   stats=_stats_from_config('HEAVY', 'Heavy'),
                   ai=ai,
                   patrol_zone=patrol_zone)
class FastEnemy(Enemy):
    """Быстрый враг: маленький, очень быстрый, 1 HP."""
    TYPE_ID = 'fast'
    @classmethod
    def create(cls, x, y, patrol_zone) -> 'FastEnemy':
        chase_r = get_config('ENEMIES_FAST_CHASE_RADIUS', 180)
        lose_r = get_config('ENEMIES_CHASE_LOSE_RADIUS', 280)
        ai = ChaseBehavior(chase_radius=chase_r, lose_radius=lose_r,
                           patrol_fallback=PatrolBehavior(repath_interval=1.2))
        return cls(x, y,
                   stats=_stats_from_config('FAST', 'Fast'),
                   ai=ai,
                   patrol_zone=patrol_zone)
