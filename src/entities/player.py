import pygame
import math
from src.core.config_loader import get_config, get_color
from src.entities.weapons import Weapon
from src.entities.player_stats import PlayerStats, unlocked_weapon_slots
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

        # Направление движения - результат W/A/S/D относительно направления
        # прицела (см. handle_input): вперёд/назад вдоль (aim_dx, aim_dy),
        # влево/вправо перпендикулярно ему. Не twin-stick - игрок вращается
        # на месте прицелом (мышь), а движение всегда "танковое" относительно
        # того, куда он сейчас смотрит.
        self.direction_x = 0
        self.direction_y = 0

        # Прицел (360°, мышь) - непрерывный юнит-вектор, источник геометрии
        # атаки/снарядов. Дефолт "смотрит вниз", как раньше facing_direction.
        self.aim_dx = 0.0
        self.aim_dy = 1.0
        # facing_direction - производная строка (ближайшее из 8 названий) для
        # формата сохранений и debug-текста. Не используется боевой геометрией.
        self.facing_direction = 'down'

        # Делегаты: здоровье и боевая система
        self._stats = PlayerStats(get_config('PLAYER_MAX_HEALTH'))
        self._combat = PlayerCombat()
        # Разлочка слотов оружия по уровню - PlayerStats не знает про
        # PlayerCombat, поэтому дёргает Player через колбэк.
        self._stats.on_level_up = self._handle_level_up

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

    def cycle_slot_weapon(self, index: int) -> bool:
        return self._combat.cycle_slot_weapon(index)

    def move_weapon(self, from_index: int, to_index: int) -> bool:
        return self._combat.move_weapon(from_index, to_index)

    def unlock_slot(self) -> bool:
        return self._combat.unlock_slot()

    # --- Патроны (делегирует PlayerCombat) ----------------------------------

    @property
    def magazine(self):
        """dict ammo_type -> кол-во в магазине (тот же объект, не копия -
        нужно save_system'у чтобы мутировать через .clear()/.update())."""
        return self._combat.magazine

    @property
    def reserve(self):
        """dict ammo_type -> кол-во в резерве."""
        return self._combat.reserve

    def reload(self) -> bool:
        return self._combat.reload()

    def add_ammo(self, ammo_type: str, amount: int, cap: int) -> None:
        self._combat.add_ammo(ammo_type, amount, cap)

    def magazine_count(self, ammo_type: str = None) -> int:
        if ammo_type is None:
            ammo_type = self.current_weapon.ammo_type
        if not ammo_type:
            return 0
        return self._combat.magazine.get(ammo_type, 0)

    def reserve_count(self, ammo_type: str = None) -> int:
        if ammo_type is None:
            ammo_type = self.current_weapon.ammo_type
        if not ammo_type:
            return 0
        return self._combat.reserve.get(ammo_type, 0)

    def _handle_level_up(self, new_level: int) -> None:
        """Колбэк из PlayerStats: открыть слоты оружия, положенные по уровню."""
        target = unlocked_weapon_slots(new_level)
        while len(self._combat.weapons) < target:
            if not self._combat.unlock_slot():
                break

    def try_attack(self):
        self._combat.try_attack()

    def get_attack_rects(self):
        """Получить все прямоугольники зон поражения текущей атаки."""
        return self._combat.get_attack_rects(self.rect, self.aim_dx, self.aim_dy)

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

    def handle_input(self, keys):
        """Обработка ввода с клавиатуры (движение). Атака направлением мыши
        считается отдельно в update_aim() - но именно её результат
        (aim_dx, aim_dy) задаёт оси движения W/A/S/D ниже: игрок вращается
        на месте прицелом, а W/S двигают его вперёд/назад вдоль этого
        направления, A/D - вбок (strafe), перпендикулярно ему. Стрелки
        движение не дают - только WASD."""
        # Сброс направления
        self.direction_x = 0
        self.direction_y = 0

        # Спринт
        self.is_sprinting = (
            self._is_key_pressed(keys, pygame.K_LSHIFT)
            or self._is_key_pressed(keys, pygame.K_RSHIFT)
        )

        # W/S - вперёд/назад вдоль вектора прицела (aim_dx, aim_dy).
        forward = 0
        if keys[pygame.K_w]:
            forward += 1
        if keys[pygame.K_s]:
            forward -= 1
        # A/D - вбок (strafe), перпендикулярно прицелу. "Вправо" при взгляде
        # (aim_dx, aim_dy) - вектор (-aim_dy, aim_dx) (экранные координаты,
        # y вниз: поворот на 90° по часовой стрелке от взгляда игрока).
        strafe = 0
        if keys[pygame.K_d]:
            strafe += 1
        if keys[pygame.K_a]:
            strafe -= 1

        # Нормализация диагонального движения (W+A/W+D/S+A/S+D)
        if forward != 0 and strafe != 0:
            forward *= 0.707  # 1/sqrt(2)
            strafe *= 0.707

        right_dx, right_dy = -self.aim_dy, self.aim_dx
        self.direction_x = forward * self.aim_dx + strafe * right_dx
        self.direction_y = forward * self.aim_dy + strafe * right_dy

        # Атака на пробел (в текущем направлении прицела - см. update_aim)
        if keys[pygame.K_SPACE]:
            self.try_attack()

    _FACING_8WAY = (
        'right', 'down_right', 'down', 'down_left',
        'left', 'up_left', 'up', 'up_right',
    )

    def update_aim(self, camera_x: float, camera_y: float) -> None:
        """Обновить направление прицела по позиции мыши - непрерывный вектор
        (360°), не завязан на движение ("как турель"). camera_x/camera_y -
        для перевода экранных координат курсора в мировые относительно игрока."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        player_screen_x = self.x - camera_x + self.width / 2
        player_screen_y = self.y - camera_y + self.height / 2
        dx = mouse_x - player_screen_x
        dy = mouse_y - player_screen_y
        dist = math.hypot(dx, dy)
        if dist < 1:
            # Курсор точно на игроке - направление не меняем (не делим на 0).
            return
        self.aim_dx = dx / dist
        self.aim_dy = dy / dist

        # facing_direction - косметика/совместимость с save-форматом и debug.
        angle = math.degrees(math.atan2(self.aim_dy, self.aim_dx)) % 360
        sector = int((angle + 22.5) // 45) % 8
        self.facing_direction = self._FACING_8WAY[sector]

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

            # Разрешаем коллизию по осям НЕЗАВИСИМО - иначе движение по
            # диагонали блокируется целиком даже если только одна из осей
            # реально упирается в стену, и юнит "залипает" на препятствии
            # при любом отклонении взгляда от перпендикуляра к стене.
            moved = False
            if new_x != self.x:
                candidate_x = pygame.Rect(int(new_x), int(self.y), self.width, self.height)
                if not world.check_collision(candidate_x):
                    self.x = new_x
                    moved = True
            if new_y != self.y:
                candidate_y = pygame.Rect(int(self.x), int(new_y), self.width, self.height)
                if not world.check_collision(candidate_y):
                    self.y = new_y
                    moved = True

            if moved:
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
        
        # Направление прицела (360°, следует за мышью) - точка на краю
        # игрока вдоль (aim_dx, aim_dy), а не одна из 8 фиксированных позиций.
        center_x = screen_x + self.width // 2
        center_y = screen_y + self.height // 2
        radius = self.width / 2 - 3
        dot_x = int(center_x + self.aim_dx * radius)
        dot_y = int(center_y + self.aim_dy * radius)
        pygame.draw.circle(screen, get_color('WHITE'), (dot_x, dot_y), 3)


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

