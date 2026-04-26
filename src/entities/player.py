import pygame
import math
from src.core.config_loader import get_config, get_color
from src.entities.weapons import Weapon, default_loadout
from src.entities.player_stats import PlayerStats
from src.entities.player_combat import PlayerCombat


class Player:
    def __init__(self, x, y):
        # Позиция игрока
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        
        # Скорость движения (как в классической Zelda)
        self.speed = 120  # пикселей в секунду
        # Множитель скорости при удержании Shift.
        self.sprint_multiplier = get_config('PLAYER_SPRINT_MULTIPLIER')
        self.is_sprinting = False

        # Направление движения
        self.direction_x = 0
        self.direction_y = 0
        self.facing_direction = 'down'
        # Были ли обе оси нажаты в прошлом кадре (для залочки диагонали)
        self._prev_both_axes = False

        # Делегаты: здоровье и боевая система
        self._stats = PlayerStats(get_config('PLAYER_MAX_HEALTH'))
        self._combat = PlayerCombat()

        # Cooldown урона от окружения
        self.last_damage_time = 0
        self.damage_cooldown = 1000

        # Прямоугольник для коллизий
        self.rect = pygame.Rect(x, y, self.width, self.height)

        # Knockback state
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0
        self.knockback_timer = 0.0
        self._kb_duration = get_config('COMBAT_PLAYER_KNOCKBACK_DURATION', 0.15)
        self._kb_speed = get_config('COMBAT_PLAYER_KNOCKBACK_SPEED', 220)

    # --- Backward-compatible API для здоровья (делегирует PlayerStats) ------

    @property
    def max_health(self):
        return self._stats.max_health

    @max_health.setter
    def max_health(self, value):
        self._stats.max_health = value

    @property
    def health(self):
        return self._stats.health

    @health.setter
    def health(self, value):
        self._stats.health = value

    def is_dead(self):
        return self._stats.is_dead()

    def take_damage(self, damage, game_stats=None, ignore_iframes=False):
        return self._stats.take_damage(damage, game_stats, ignore_iframes=ignore_iframes)

    def heal(self, amount):
        self._stats.heal(amount)

    def get_health_percentage(self):
        return self._stats.get_health_percentage()

    # Прогрессия
    @property
    def stats(self):
        return self._stats

    @property
    def level(self):
        return self._stats.level

    @property
    def xp(self):
        return self._stats.xp

    @property
    def coins(self):
        return self._stats.coins

    @property
    def damage_bonus(self):
        return self._stats.damage_bonus

    @property
    def is_invulnerable(self):
        return self._stats.is_invulnerable

    def apply_knockback(self, from_x: float, from_y: float) -> None:
        """Применить knockback от точки (from_x, from_y) к игроку."""
        dx = self.x - from_x
        dy = self.y - from_y
        dist = math.hypot(dx, dy)
        if dist < 1:
            dx, dy, dist = 0, -1, 1  # дефолт - вверх
        self.knockback_vx = (dx / dist) * self._kb_speed
        self.knockback_vy = (dy / dist) * self._kb_speed
        self.knockback_timer = self._kb_duration

    # --- Backward-compatible API для боя (делегирует PlayerCombat) ----------

    @property
    def attacking(self):
        return self._combat.attacking

    @attacking.setter
    def attacking(self, value):
        self._combat.attacking = value

    @property
    def attack_timer(self):
        return self._combat.attack_timer

    @attack_timer.setter
    def attack_timer(self, value):
        self._combat.attack_timer = value

    @property
    def last_attack_time(self):
        return self._combat.last_attack_time

    @last_attack_time.setter
    def last_attack_time(self, value):
        self._combat.last_attack_time = value

    @property
    def attack_id(self):
        return self._combat.attack_id

    @attack_id.setter
    def attack_id(self, value):
        self._combat.attack_id = value

    @property
    def weapons(self):
        return self._combat.weapons

    @weapons.setter
    def weapons(self, value):
        self._combat.weapons = value

    @property
    def current_weapon_index(self):
        return self._combat.current_weapon_index

    @current_weapon_index.setter
    def current_weapon_index(self, value):
        self._combat.current_weapon_index = value

    @property
    def current_weapon(self) -> Weapon:
        return self._combat.current_weapon

    def switch_weapon(self, index: int) -> bool:
        return self._combat.switch_weapon(index)

    def try_attack(self):
        self._combat.try_attack()

    def get_attack_rects(self):
        """Получить все прямоугольники зон поражения текущей атаки."""
        return self._combat.get_attack_rects(self.rect, self.facing_direction)

    def get_attack_rect(self):
        """Совместимость: вернуть первую зону атаки или None."""
        rects = self.get_attack_rects()
        return rects[0] if rects else None

    # --- Ввод и логика движения -------------------------------------------

    @staticmethod
    def _is_key_pressed(keys, code):
        """Безопасное чтение состояния клавиши (для моков в тестах)."""
        try:
            return bool(keys[code])
        except (KeyError, IndexError):
            return False

    def _set_cardinal_facing(self):
        """Установить кардинальное facing из текущего direction."""
        if self.direction_x == -1:
            self.facing_direction = 'left'
        elif self.direction_x == 1:
            self.facing_direction = 'right'
        elif self.direction_y == -1:
            self.facing_direction = 'up'
        elif self.direction_y == 1:
            self.facing_direction = 'down'

    def handle_input(self, keys):
        """Обработка ввода с клавиатуры"""
        # Сброс направления
        self.direction_x = 0
        self.direction_y = 0

        # Спринт
        self.is_sprinting = (
            self._is_key_pressed(keys, pygame.K_LSHIFT)
            or self._is_key_pressed(keys, pygame.K_RSHIFT)
        )

        # Движение по 8 направлениям
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction_x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction_y = 1
            
        # Определяем направление взгляда на основе движения (8 направлений).
        # Логика:
        #  - Обе оси нажаты → facing = диагональ (всегда)
        #  - Одна ось нажата И в прошлом кадре были обе → "отпускание" → facing сохраняется
        #  - Одна ось нажата И в прошлом кадре тоже одна → facing = кардинальное
        #  - Ничего не нажато → facing сохраняется (можно бить стоя)
        both_axes = (self.direction_x != 0 and self.direction_y != 0)

        if both_axes:
            # Чистая диагональ
            if self.direction_x == -1 and self.direction_y == -1:
                self.facing_direction = 'up_left'
            elif self.direction_x == 1 and self.direction_y == -1:
                self.facing_direction = 'up_right'
            elif self.direction_x == -1 and self.direction_y == 1:
                self.facing_direction = 'down_left'
            else:
                self.facing_direction = 'down_right'
        elif self.direction_x != 0 or self.direction_y != 0:
            # Одна ось нажата
            if not self._prev_both_axes:
                # В прошлом кадре тоже была одна ось (или ноль) → обновляем
                self._set_cardinal_facing()
            # Иначе: в прошлом кадре были обе → только что отпустили вторую
            # клавишу → сохраняем диагональный facing (залочка на 1 кадр)
        # Ничего не нажато → facing остаётся

        self._prev_both_axes = both_axes

        # Нормализация диагонального движения
        if self.direction_x != 0 and self.direction_y != 0:
            self.direction_x *= 0.707  # 1/sqrt(2)
            self.direction_y *= 0.707
            
        # Атака на пробел
        if keys[pygame.K_SPACE]:
            self.try_attack()

    def update(self, dt, world, game_stats=None):
        """Обновление состояния игрока"""
        # Тик i-frame таймера
        self._stats.update(dt)

        # Обновление атаки
        self._combat.update_attack()

        # Knockback приоритетнее ввода
        if self.knockback_timer > 0:
            self.knockback_timer -= dt
            new_x = self.x + self.knockback_vx * dt
            new_y = self.y + self.knockback_vy * dt
            new_x = max(0, min(new_x, world.width - self.width))
            new_y = max(0, min(new_y, world.height - self.height))
            temp_rect = pygame.Rect(int(new_x), int(new_y), self.width, self.height)
            if not world.check_collision(temp_rect):
                self.x = new_x
                self.y = new_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
            if self.knockback_timer <= 0:
                self.knockback_vx = 0.0
                self.knockback_vy = 0.0
            return

        # Движение
        if not self.attacking:
            current_tile = world.get_terrain_at(self.x + self.width//2, self.y + self.height//2)
            speed_modifier = current_tile.speed_modifier if current_tile else 1.0
            sprint = self.sprint_multiplier if self.is_sprinting else 1.0
            effective_speed = self.speed * speed_modifier * sprint
            
            new_x = self.x + self.direction_x * effective_speed * dt
            new_y = self.y + self.direction_y * effective_speed * dt
            
            new_x = max(0, min(new_x, world.width - self.width))
            new_y = max(0, min(new_y, world.height - self.height))
            
            temp_rect = pygame.Rect(int(new_x), int(new_y), self.width, self.height)
            
            if not world.check_collision(temp_rect):
                self.x = new_x
                self.y = new_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                
                new_tile = world.get_terrain_at(self.x + self.width//2, self.y + self.height//2)
                if new_tile and new_tile.damages_player:
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_damage_time > self.damage_cooldown:
                        self.take_damage(new_tile.damage_amount, game_stats,
                                        ignore_iframes=True)
                        self.last_damage_time = current_time

    # --- Отрисовка ---------------------------------------------------------

    def draw(self, screen, camera_x=0, camera_y=0):
        """Отрисовка игрока"""
        # Мигание при i-frames (пропускаем каждый чётный кадр)
        if self.is_invulnerable:
            # ~10 миганий/сек при 60fps: пропускаем каждые 3 кадра
            import time
            if int(time.time() * 10) % 2 == 0:
                # Рисуем полупрозрачно — skip кадра
                return

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        color = get_color('RED') if self.attacking else get_color('GREEN')
        pygame.draw.rect(screen, color, (screen_x, screen_y, self.width, self.height))
        
        # Направление взгляда
        center_x = screen_x + self.width // 2
        center_y = screen_y + self.height // 2
        
        if self.facing_direction == 'up':
            pygame.draw.circle(screen, get_color('WHITE'), (center_x, screen_y + 5), 3)
        elif self.facing_direction == 'down':
            pygame.draw.circle(screen, get_color('WHITE'), (center_x, screen_y + self.height - 5), 3)
        elif self.facing_direction == 'left':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + 5, center_y), 3)
        elif self.facing_direction == 'right':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + self.width - 5, center_y), 3)
        elif self.facing_direction == 'up_left':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + 5, screen_y + 5), 3)
        elif self.facing_direction == 'up_right':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + self.width - 5, screen_y + 5), 3)
        elif self.facing_direction == 'down_left':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + 5, screen_y + self.height - 5), 3)
        elif self.facing_direction == 'down_right':
            pygame.draw.circle(screen, get_color('WHITE'), (screen_x + self.width - 5, screen_y + self.height - 5), 3)
        
        # Зоны атаки
        if self.attacking:
            weapon = self.current_weapon
            for attack_rect in self.get_attack_rects():
                attack_screen_rect = pygame.Rect(
                    attack_rect.x - camera_x,
                    attack_rect.y - camera_y,
                    attack_rect.width,
                    attack_rect.height
                )
                pygame.draw.rect(screen, weapon.color, attack_screen_rect, 2)

