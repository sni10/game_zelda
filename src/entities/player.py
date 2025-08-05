import pygame
import math
from src.core.config_loader import get_config, get_color


class Player:
    def __init__(self, x, y):
        # Позиция игрока
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        
        # Скорость движения (как в классической Zelda)
        self.speed = 120  # пикселей в секунду
        
        # Направление движения
        self.direction_x = 0
        self.direction_y = 0
        self.facing_direction = 'down'  # направление взгляда для атаки (8 направлений)
        
        # Система здоровья
        self.max_health = 100
        self.health = self.max_health
        self.last_damage_time = 0
        self.damage_cooldown = 1000  # миллисекунды между уроном от окружения
        
        # Система атаки
        self.attacking = False
        self.attack_duration = 300  # миллисекунды
        self.attack_timer = 0
        self.attack_cooldown = 100  # миллисекунды между атаками
        self.last_attack_time = 0
        
        # Прямоугольник для коллизий
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def handle_input(self, keys):
        """Обработка ввода с клавиатуры"""
        # Сброс направления
        self.direction_x = 0
        self.direction_y = 0
        
        # Движение по 8 направлениям
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction_x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction_x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction_y = 1
            
        # Определяем направление взгляда на основе движения (8 направлений)
        if self.direction_x != 0 or self.direction_y != 0:
            if self.direction_x == -1 and self.direction_y == -1:
                self.facing_direction = 'up_left'
            elif self.direction_x == 1 and self.direction_y == -1:
                self.facing_direction = 'up_right'
            elif self.direction_x == -1 and self.direction_y == 1:
                self.facing_direction = 'down_left'
            elif self.direction_x == 1 and self.direction_y == 1:
                self.facing_direction = 'down_right'
            elif self.direction_x == -1:
                self.facing_direction = 'left'
            elif self.direction_x == 1:
                self.facing_direction = 'right'
            elif self.direction_y == -1:
                self.facing_direction = 'up'
            elif self.direction_y == 1:
                self.facing_direction = 'down'
            
        # Нормализация диагонального движения
        if self.direction_x != 0 and self.direction_y != 0:
            # Уменьшаем скорость по диагонали для равномерного движения
            self.direction_x *= 0.707  # 1/sqrt(2)
            self.direction_y *= 0.707
            
        # Атака на пробел
        if keys[pygame.K_SPACE]:
            self.try_attack()
    
    def try_attack(self):
        """Попытка атаки"""
        current_time = pygame.time.get_ticks()
        if not self.attacking and current_time - self.last_attack_time > self.attack_cooldown:
            self.attacking = True
            self.attack_timer = current_time
            self.last_attack_time = current_time
    
    def update(self, dt, world, game_stats=None):
        """Обновление состояния игрока"""
        # Обновление атаки
        if self.attacking:
            current_time = pygame.time.get_ticks()
            if current_time - self.attack_timer > self.attack_duration:
                self.attacking = False
        
        # Движение
        if not self.attacking:  # Нельзя двигаться во время атаки
            # Проверяем текущий ландшафт для модификации скорости
            current_tile = world.get_terrain_at(self.x + self.width//2, self.y + self.height//2)
            speed_modifier = current_tile.speed_modifier if current_tile else 1.0
            effective_speed = self.speed * speed_modifier
            
            # Вычисление новой позиции
            new_x = self.x + self.direction_x * effective_speed * dt
            new_y = self.y + self.direction_y * effective_speed * dt
            
            # Ограничение движения границами мира
            new_x = max(0, min(new_x, world.width - self.width))
            new_y = max(0, min(new_y, world.height - self.height))
            
            # Создаем временный rect для проверки коллизий
            temp_rect = pygame.Rect(int(new_x), int(new_y), self.width, self.height)
            
            # Проверка коллизий с препятствиями
            if not world.check_collision(temp_rect):
                # Обновление позиции только если нет коллизий
                self.x = new_x
                self.y = new_y
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                
                # Проверяем урон от ландшафта
                new_tile = world.get_terrain_at(self.x + self.width//2, self.y + self.height//2)
                if new_tile and new_tile.damages_player:
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_damage_time > self.damage_cooldown:
                        self.take_damage(new_tile.damage_amount, game_stats)
                        self.last_damage_time = current_time
    
    def get_attack_rect(self):
        """Получить прямоугольник атаки"""
        if not self.attacking:
            return None
            
        attack_range = 40
        attack_width = 30
        attack_height = 30
        
        if self.facing_direction == 'up':
            return pygame.Rect(self.rect.centerx - attack_width//2, 
                             self.rect.top - attack_range, 
                             attack_width, attack_height)
        elif self.facing_direction == 'down':
            return pygame.Rect(self.rect.centerx - attack_width//2, 
                             self.rect.bottom, 
                             attack_width, attack_height)
        elif self.facing_direction == 'left':
            return pygame.Rect(self.rect.left - attack_range, 
                             self.rect.centery - attack_height//2, 
                             attack_width, attack_height)
        elif self.facing_direction == 'right':
            return pygame.Rect(self.rect.right, 
                             self.rect.centery - attack_height//2, 
                             attack_width, attack_height)
        elif self.facing_direction == 'up_left':
            return pygame.Rect(self.rect.left - attack_range//2, 
                             self.rect.top - attack_range//2, 
                             attack_width, attack_height)
        elif self.facing_direction == 'up_right':
            return pygame.Rect(self.rect.right - attack_width//2, 
                             self.rect.top - attack_range//2, 
                             attack_width, attack_height)
        elif self.facing_direction == 'down_left':
            return pygame.Rect(self.rect.left - attack_range//2, 
                             self.rect.bottom - attack_height//2, 
                             attack_width, attack_height)
        elif self.facing_direction == 'down_right':
            return pygame.Rect(self.rect.right - attack_width//2, 
                             self.rect.bottom - attack_height//2, 
                             attack_width, attack_height)
        return None
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Отрисовка игрока"""
        # Позиция на экране с учетом камеры
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Цвет игрока (зеленый, красный во время атаки)
        color = get_color('RED') if self.attacking else get_color('GREEN')
        
        # Рисуем игрока как прямоугольник
        pygame.draw.rect(screen, color, (screen_x, screen_y, self.width, self.height))
        
        # Рисуем направление взгляда
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
        
        # Рисуем зону атаки
        if self.attacking:
            attack_rect = self.get_attack_rect()
            if attack_rect:
                attack_screen_rect = pygame.Rect(
                    attack_rect.x - camera_x,
                    attack_rect.y - camera_y,
                    attack_rect.width,
                    attack_rect.height
                )
                pygame.draw.rect(screen, (255, 255, 0, 128), attack_screen_rect, 2)
    
    def is_dead(self):
        """Проверка, мертв ли игрок"""
        return self.health <= 0
    
    def take_damage(self, damage, game_stats=None):
        """Нанести урон игроку"""
        if not self.is_dead():
            self.health -= damage
            if self.health < 0:
                self.health = 0
            
            # Уведомляем статистику о полученном уроне
            if game_stats:
                game_stats.record_damage_taken(damage)
    
    def heal(self, amount):
        """Восстановить здоровье игрока"""
        if not self.is_dead():
            self.health += amount
            if self.health > self.max_health:
                self.health = self.max_health
    
    def get_health_percentage(self):
        """Получить процент здоровья (0.0 - 1.0)"""
        return self.health / self.max_health if self.max_health > 0 else 0.0