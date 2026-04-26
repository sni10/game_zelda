import pygame
import os
from src.core.config_loader import get_config, get_color


class MainMenu:
    def __init__(self):
        # Базовые пункты меню
        self.base_menu_items = ["Новая игра"]
        self.selected_index = 0
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
        
        # Обновляем список пунктов меню в зависимости от наличия сохранений
        self.update_menu_items()
    
    def has_saves(self):
        """Проверяет наличие любых сохранений (quicksave или manual-слотов)."""
        saves_dir = "saves"
        if not os.path.exists(saves_dir):
            return False
        # Quicksave / любые .json в корне
        if any(f.endswith('.json') for f in os.listdir(saves_dir)):
            return True
        # Manual-слоты в saves/manual/
        manual_dir = os.path.join(saves_dir, "manual")
        if os.path.isdir(manual_dir):
            if any(f.endswith('.json') for f in os.listdir(manual_dir)):
                return True
        return False
    
    def has_quicksave(self):
        """Проверяет наличие quicksave файла"""
        return os.path.exists("saves/quicksave.json")
    
    def update_menu_items(self):
        """Обновляет список пунктов меню в зависимости от наличия сохранений"""
        self.menu_items = ["Новая игра"]
        
        # Добавляем "Продолжить игру" только если есть quicksave
        if self.has_quicksave():
            self.menu_items.append("Продолжить игру")
        
        # Добавляем "Загрузить игру" если есть любые сохранения
        if self.has_saves():
            self.menu_items.append("Загрузить игру")
        
        # Всегда добавляем "Выход"
        self.menu_items.append("Выход")
        
        # Корректируем выбранный индекс если он выходит за границы
        if self.selected_index >= len(self.menu_items):
            self.selected_index = len(self.menu_items) - 1
    
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
        if self.selected_index < 0 or self.selected_index >= len(self.menu_items):
            return None
        
        selected_item = self.menu_items[self.selected_index]
        
        if selected_item == "Новая игра":
            return "new_game"
        elif selected_item == "Продолжить игру":
            return "continue_game"
        elif selected_item == "Загрузить игру":
            return "load_game"
        elif selected_item == "Выход":
            return "exit"
        
        return None
    
    def draw(self, screen):
        """Отрисовка меню"""
        # Обновляем список пунктов меню при каждой отрисовке
        self.update_menu_items()
        
        screen.fill(get_color('BLACK'))
        
        # Заголовок с улучшенной стилизацией
        title_text = self.title_font.render("ZELDA-LIKE GAME", True, get_color('WHITE'))
        title_rect = title_text.get_rect(center=(get_config('WIDTH') // 2, 120))
        screen.blit(title_text, title_rect)
        
        # Подзаголовок
        subtitle_font = pygame.font.Font(None, 32)
        subtitle_text = subtitle_font.render("🎮 Приключение начинается здесь", True, get_color('GRAY'))
        subtitle_rect = subtitle_text.get_rect(center=(get_config('WIDTH') // 2, 170))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Пункты меню с улучшенной стилизацией
        menu_start_y = 250
        for i, item in enumerate(self.menu_items):
            y_pos = menu_start_y + i * 70
            
            # Цвет и эффекты для выбранного пункта
            if i == self.selected_index:
                color = get_color('YELLOW')
                # Рамка вокруг выбранного пункта
                menu_rect = pygame.Rect(get_config('WIDTH') // 2 - 150, y_pos - 25, 300, 50)
                pygame.draw.rect(screen, get_color('DARK_GRAY'), menu_rect, 2)
                # Стрелочки для выбранного пункта
                arrow_font = pygame.font.Font(None, 48)
                left_arrow = arrow_font.render("►", True, get_color('YELLOW'))
                right_arrow = arrow_font.render("◄", True, get_color('YELLOW'))
                screen.blit(left_arrow, (get_config('WIDTH') // 2 - 200, y_pos - 15))
                screen.blit(right_arrow, (get_config('WIDTH') // 2 + 170, y_pos - 15))
            else:
                color = get_color('WHITE')
            
            # Отрисовка текста пункта меню
            text = self.font.render(item, True, color)
            text_rect = text.get_rect(center=(get_config('WIDTH') // 2, y_pos))
            screen.blit(text, text_rect)
        
        # Инструкции внизу экрана
        instruction_font = pygame.font.Font(None, 24)
        instructions = [
            "↑↓ - Навигация по меню",
            "Enter - Выбрать",
            "ESC - Выход (в игре - возврат в меню)"
        ]
        
        instruction_y = get_config('HEIGHT') - 80
        for instruction in instructions:
            instruction_text = instruction_font.render(instruction, True, get_color('GRAY'))
            instruction_rect = instruction_text.get_rect(center=(get_config('WIDTH') // 2, instruction_y))
            screen.blit(instruction_text, instruction_rect)
            instruction_y += 25