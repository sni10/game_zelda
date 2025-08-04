import pygame
from src.core.settings import *


class Enemy:
    """Базовый класс для врагов (для будущей реализации)"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def update(self, dt):
        """Обновление состояния врага"""
        pass
        
    def draw(self, screen, camera_x=0, camera_y=0):
        """Отрисовка врага"""
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.rect(screen, RED, (screen_x, screen_y, self.width, self.height))