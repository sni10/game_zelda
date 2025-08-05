import pygame
import sys
from src.core.config_loader import load_config, get_config, get_color
from src.core.game_states import GameState
from src.core.game_stats import GameStats
from src.ui.menu import MainMenu
from src.ui.game_over import GameOverScreen
from src.utils.debug import debug
from src.entities.player import Player
from src.world.world import World
from src.systems.save_system import SaveSystem


class Game:
    def __init__(self):
        # Загрузка конфигурации
        self.config = load_config()
        
        # Инициализация Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((get_config('WIDTH'), get_config('HEIGHT')))
        pygame.display.set_caption("Zelda-like Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Состояние игры
        self.state = GameState.MENU
        
        # Главное меню
        self.menu = MainMenu()
        
        # Игровые объекты (инициализируются при начале новой игры)
        self.world = None
        self.player = None
        self.game_stats = None
        self.game_over_screen = None
        
        # Переменные для отслеживания времени
        self.last_time = pygame.time.get_ticks()
        
        # Отладочная информация
        self.show_debug = False
        
        # Система сохранений
        self.save_system = SaveSystem()

    def start_new_game(self):
        """Инициализация новой игры"""
        # Создание игрового мира
        self.world = World(width=get_config('WORLD_WIDTH'), height=get_config('WORLD_HEIGHT'))
        
        # Создание игрока в стартовой позиции из карты
        player_start_x, player_start_y = self.world.get_player_start_position()
        self.player = Player(player_start_x, player_start_y)
        
        # Инициализация статистики игры
        self.game_stats = GameStats()
        
        # Инициализация Game Over экрана
        self.game_over_screen = GameOverScreen(
            get_config('WIDTH'), 
            get_config('HEIGHT'), 
            self.game_stats
        )
        
        # Переход в игровое состояние
        self.state = GameState.PLAYING

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    # Обработка событий в меню
                    action = self.menu.handle_input(event)
                    if action == "new_game":
                        self.start_new_game()
                    elif action == "continue_game":
                        # Загрузка quicksave
                        self.quickload()
                    elif action == "load_game":
                        # TODO: Реализовать диалог выбора сохранений при реализации Issue #16
                        print("Загрузить игру - функция будет реализована в Issue #16")
                        # Пока что запускаем новую игру
                        self.start_new_game()
                    elif action == "exit":
                        self.running = False
                elif self.state == GameState.PLAYING:
                    # Обработка событий в игре
                    if event.key == pygame.K_F1:
                        self.show_debug = not self.show_debug
                    elif event.key == pygame.K_F5:
                        # Быстрое сохранение
                        self.quicksave()
                    elif event.key == pygame.K_F9:
                        # Быстрая загрузка
                        self.quickload()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                elif self.state == GameState.GAME_OVER:
                    # Обработка событий на экране Game Over
                    if self.game_over_screen:
                        action = self.game_over_screen.handle_input(event)
                        if action == "MENU":
                            self.state = GameState.MENU
                        elif action == "QUIT":
                            self.running = False

    def update(self, dt):
        """Обновление игровой логики"""
        if self.state == GameState.PLAYING and self.player and self.world:
            # Проверка смерти игрока
            if self.player.is_dead():
                self.game_stats.record_death()
                self.state = GameState.GAME_OVER
                return
            
            # Получение состояния клавиш
            keys = pygame.key.get_pressed()
            
            # Обработка ввода игрока
            self.player.handle_input(keys)
            
            # Обновление игрока (коллизии теперь проверяются внутри player.update)
            self.player.update(dt, self.world, self.game_stats)
            
            # Обновление статистики
            if self.game_stats:
                self.game_stats.update_position(self.player.x, self.player.y)
            
            # Обновление камеры
            self.world.update_camera(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                get_config('WIDTH'), get_config('HEIGHT')
            )

    def draw(self):
        """Отрисовка игры"""
        if self.state == GameState.MENU:
            # Отрисовка меню
            self.menu.draw(self.screen)
        elif self.state == GameState.PLAYING and self.player and self.world:
            # Очистка экрана
            self.screen.fill(get_color('BLACK'))
            
            # Отрисовка мира
            self.world.draw(self.screen, self.player.x, self.player.y)
            
            # Отрисовка игрока
            self.player.draw(self.screen, self.world.camera_x, self.world.camera_y)
            
            # Отрисовка UI (полоска здоровья)
            self.draw_health_bar()
            
            # Отладочная информация
            if self.show_debug:
                debug_info = [
                    f"Player: ({int(self.player.x)}, {int(self.player.y)})",
                    f"Camera: ({int(self.world.camera_x)}, {int(self.world.camera_y)})",
                    f"Direction: {self.player.facing_direction}",
                    f"Attacking: {self.player.attacking}",
                    f"FPS: {int(self.clock.get_fps())}",
                    "Controls: WASD/Arrows - Move, Space - Attack, F1 - Debug, ESC - Menu"
                ]
                
                y_offset = 10
                for info in debug_info:
                    debug(info, y=y_offset)
                    y_offset += 20
            else:
                # Показываем базовые инструкции
                debug("Press F1 for debug info, ESC for menu", y=get_config('HEIGHT') - 30)
        elif self.state == GameState.GAME_OVER:
            # Отрисовка экрана Game Over
            if self.game_over_screen:
                self.game_over_screen.draw(self.screen)
        
        # Обновление дисплея
        pygame.display.flip()

    def draw_health_bar(self):
        """Отрисовка полоски здоровья игрока"""
        # Параметры полоски здоровья
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 10
        border_width = 2
        
        # Вычисляем процент здоровья
        health_percentage = self.player.health / self.player.max_health
        health_bar_width = int(bar_width * health_percentage)
        
        # Рисуем фон полоски (темно-серый)
        pygame.draw.rect(self.screen, get_color('DARK_GRAY'), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Рисуем полоску здоровья (зеленый)
        if health_bar_width > 0:
            pygame.draw.rect(self.screen, get_color('GREEN'), 
                            (bar_x, bar_y, health_bar_width, bar_height))
        
        # Рисуем тонкую рамочку
        pygame.draw.rect(self.screen, get_color('WHITE'), 
                        (bar_x - border_width, bar_y - border_width, 
                         bar_width + border_width * 2, bar_height + border_width * 2), 
                        border_width)
        
        # Добавляем текст с числовым значением здоровья
        font = pygame.font.Font(None, 24)
        health_text = f"{int(self.player.health)}/{int(self.player.max_health)}"
        text_surface = font.render(health_text, True, get_color('WHITE'))
        text_x = bar_x + bar_width + 10
        text_y = bar_y + (bar_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

    def quicksave(self):
        """Быстрое сохранение игры (F5)"""
        if self.player and self.world:
            success = self.save_system.save_game(self.player, self.world)
            if success:
                # Показываем уведомление об успешном сохранении
                print("Игра сохранена! (F5)")
            else:
                print("Ошибка сохранения!")
        else:
            print("Нет активной игры для сохранения!")

    def quickload(self):
        """Быстрая загрузка игры (F9)"""
        if not self.save_system.quicksave_exists():
            print("Файл быстрого сохранения не найден!")
            return
        
        save_data = self.save_system.load_game()
        if save_data:
            # Если игра не запущена, создаем новый мир и игрока
            if not self.player or not self.world:
                self.world = World(width=get_config('WORLD_WIDTH'), height=get_config('WORLD_HEIGHT'))
                # Создаем игрока с временными координатами
                self.player = Player(0, 0)
            
            # Применяем загруженные данные
            self.save_system.apply_save_data_to_player(self.player, save_data)
            self.save_system.apply_save_data_to_world(self.world, save_data)
            
            # Переходим в игровое состояние
            self.state = GameState.PLAYING
            print("Игра загружена! (F9)")
        else:
            print("Ошибка загрузки!")

    def run(self):
        """Основной игровой цикл"""
        while self.running:
            # Вычисление времени кадра
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0  # Конвертация в секунды
            self.last_time = current_time
            
            # Ограничение dt для стабильности
            dt = min(dt, 1.0 / 30.0)  # Максимум 30 FPS для физики
            
            # Обработка событий
            self.handle_events()
            
            # Обновление игры
            self.update(dt)
            
            # Отрисовка
            self.draw()
            
            # Ограничение FPS
            self.clock.tick(get_config('FPS'))
        
        # Завершение работы
        pygame.quit()
        sys.exit()

