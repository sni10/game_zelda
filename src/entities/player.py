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
        self.facing_direction = 'down'  # направление взгляда для атаки
        
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
            self.facing_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction_x = 1
            self.facing_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction_y = -1
            self.facing_direction = 'up'
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction_y = 1
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
    
    def update(self, dt, world_width, world_height):
        """Обновление состояния игрока"""
        # Обновление атаки
        if self.attacking:
            current_time = pygame.time.get_ticks()
            if current_time - self.attack_timer > self.attack_duration:
                self.attacking = False
        
        # Движение
        if not self.attacking:  # Нельзя двигаться во время атаки
            # Вычисление новой позиции
            new_x = self.x + self.direction_x * self.speed * dt
            new_y = self.y + self.direction_y * self.speed * dt
            
            # Ограничение движения границами мира
            new_x = max(0, min(new_x, world_width - self.width))
            new_y = max(0, min(new_y, world_height - self.height))
            
            # Обновление позиции
            self.x = new_x
            self.y = new_y
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
    
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