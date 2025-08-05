import pygame
from src.core.config_loader import get_config, get_color


class MainMenu:
    def __init__(self):
        self.menu_items = ["Новая игра", "Выход"]
        self.selected_index = 0
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
    
    def handle_input(self, event):
        """Обработка ввода в меню"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN:
                return self.get_selected_action()
        return None
    
    def get_selected_action(self):
        """Возвращает действие для выбранного пункта меню"""
        if self.selected_index == 0:
            return "new_game"
        elif self.selected_index == 1:
            return "exit"
        return None
    
    def draw(self, screen):
        """Отрисовка меню"""
        screen.fill(get_color('BLACK'))
        
        # Заголовок
        title_text = self.title_font.render("ZELDA-LIKE GAME", True, get_color('WHITE'))
        title_rect = title_text.get_rect(center=(get_config('WIDTH') // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Пункты меню
        for i, item in enumerate(self.menu_items):
            color = get_color('YELLOW') if i == self.selected_index else get_color('WHITE')
            text = self.font.render(item, True, color)
            text_rect = text.get_rect(center=(get_config('WIDTH') // 2, 300 + i * 60))
            screen.blit(text, text_rect)