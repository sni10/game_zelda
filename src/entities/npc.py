import pygame
from src.core.settings import *


class NPC:
    """Базовый класс для NPC (для будущей реализации)"""
    def __init__(self, x, y, name="NPC"):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.name = name
        self.dialogue = ["Привет, путешественник!"]
        self.dialogue_index = 0
        
    def interact(self):
        """Взаимодействие с NPC"""
        if self.dialogue_index < len(self.dialogue):
            message = self.dialogue[self.dialogue_index]
            self.dialogue_index += 1
            return message
        return None
        
    def draw(self, screen, camera_x=0, camera_y=0):
        """Отрисовка NPC"""
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.rect(screen, (0, 0, 255), (screen_x, screen_y, self.width, self.height))