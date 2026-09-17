import pygame
from src.core.config_loader import get_color


class GameOverScreen:
    """Экран Game Over при смерти игрока"""

    def __init__(self, screen_width, screen_height, game_stats=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.game_stats = game_stats

        # Шрифты
        self.title_font = pygame.font.Font(None, 72)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Состояние UI
        self.selected_option = 0
        self.options = ["Вернуться в меню", "Выйти из игры"]

        # Цвета
        self.bg_color = (0, 0, 0, 180)  # Полупрозрачный черный
        self.text_color = get_color("WHITE")
        self.selected_color = get_color("YELLOW")
        self.stats_color = get_color("GRAY")

    def handle_input(self, event):
        """Обработка ввода на экране Game Over"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = (self.selected_option - 1) % len(self.options)
                return None
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = (self.selected_option + 1) % len(self.options)
                return None
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.selected_option == 0:
                    return "MENU"  # Вернуться в главное меню
                elif self.selected_option == 1:
                    return "QUIT"  # Выйти из игры
        return None

    def draw(self, screen):
        """Отрисовка экрана Game Over"""
        # Полупрозрачный фон
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Центр экрана
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Заголовок "💀 GAME OVER"
        title_text = self.title_font.render("💀 GAME OVER", True, get_color("RED"))
        title_rect = title_text.get_rect(center=(center_x, center_y - 150))
        screen.blit(title_text, title_rect)

        # Сообщение о смерти
        death_text = self.text_font.render("Вы погибли!", True, self.text_color)
        death_rect = death_text.get_rect(center=(center_x, center_y - 100))
        screen.blit(death_text, death_rect)

        # Статистика игры (если доступна)
        if self.game_stats:
            stats_y = center_y - 50

            stats_lines = [
                f"Время игры: {self.game_stats.get_play_time_formatted()}",
                f"Убито врагов: {self.game_stats.enemies_killed}",
                f"Собрано предметов: {self.game_stats.items_collected}",
                f"Нанесен урон: {self.game_stats.damage_dealt}",
                f"Получен урон: {self.game_stats.damage_taken}",
            ]

            for i, line in enumerate(stats_lines):
                stats_text = self.small_font.render(line, True, self.stats_color)
                stats_rect = stats_text.get_rect(center=(center_x, stats_y + i * 25))
                screen.blit(stats_text, stats_rect)

        # Опции меню
        options_y = center_y + 80
        for i, option in enumerate(self.options):
            color = (
                self.selected_color if i == self.selected_option else self.text_color
            )
            option_text = self.text_font.render(option, True, color)
            option_rect = option_text.get_rect(center=(center_x, options_y + i * 50))
            screen.blit(option_text, option_rect)

            # Стрелка для выбранной опции
            if i == self.selected_option:
                arrow_text = self.text_font.render("►", True, self.selected_color)
                arrow_rect = arrow_text.get_rect(
                    center=(center_x - 120, options_y + i * 50)
                )
                screen.blit(arrow_text, arrow_rect)

        # Подсказка по управлению
        help_text = self.small_font.render(
            "WASD/Стрелки: Навигация | Enter/Пробел: Выбор", True, self.stats_color
        )
        help_rect = help_text.get_rect(center=(center_x, self.screen_height - 30))
        screen.blit(help_text, help_rect)
