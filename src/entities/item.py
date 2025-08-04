import pygame
from src.core.settings import *


class Item:
    """Базовый класс для предметов (для будущей реализации)"""
    def __init__(self, x, y, item_type="generic"):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.item_type = item_type
        self.collected = False
        
    def collect(self):
        """Собрать предмет"""
        self.collected = True
        
    def draw(self, screen, camera_x=0, camera_y=0):
        """Отрисовка предмета"""
        if not self.collected:
            screen_x = int(self.x - camera_x)
            screen_y = int(self.y - camera_y)
            pygame.draw.rect(screen, YELLOW, (screen_x, screen_y, self.width, self.height))