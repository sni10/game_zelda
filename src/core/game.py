import pygame
import sys
from src.core.config_loader import load_config, get_config, get_color
from src.utils.debug import debug
from src.entities.player import Player
from src.world.world import World


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
        
        # Создание игрового мира
        self.world = World(width=get_config('WORLD_WIDTH'), height=get_config('WORLD_HEIGHT'))
        
        # Создание игрока в центре мира
        player_start_x = self.world.width // 2
        player_start_y = self.world.height // 2
        self.player = Player(player_start_x, player_start_y)
        
        # Переменные для отслеживания времени
        self.last_time = pygame.time.get_ticks()
        
        # Отладочная информация
        self.show_debug = False

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self, dt):
        """Обновление игровой логики"""
        # Получение состояния клавиш
        keys = pygame.key.get_pressed()
        
        # Обработка ввода игрока
        self.player.handle_input(keys)
        
        # Сохранение старой позиции для проверки коллизий
        old_x = self.player.x
        old_y = self.player.y
        
        # Обновление игрока
        self.player.update(dt, self.world.width, self.world.height)
        
        # Проверка коллизий с препятствиями
        if self.world.check_collision(self.player.rect):
            # Возврат к старой позиции при коллизии
            self.player.x = old_x
            self.player.y = old_y
            self.player.rect.x = int(old_x)
            self.player.rect.y = int(old_y)
        
        # Обновление камеры
        self.world.update_camera(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            get_config('WIDTH'), get_config('HEIGHT')
        )

    def draw(self):
        """Отрисовка игры"""
        # Очистка экрана
        self.screen.fill(get_color('BLACK'))
        
        # Отрисовка мира
        self.world.draw(self.screen, self.player.x, self.player.y)
        
        # Отрисовка игрока
        self.player.draw(self.screen, self.world.camera_x, self.world.camera_y)
        
        # Отладочная информация
        if self.show_debug:
            debug_info = [
                f"Player: ({int(self.player.x)}, {int(self.player.y)})",
                f"Camera: ({int(self.world.camera_x)}, {int(self.world.camera_y)})",
                f"Direction: {self.player.facing_direction}",
                f"Attacking: {self.player.attacking}",
                f"FPS: {int(self.clock.get_fps())}",
                "Controls: WASD/Arrows - Move, Space - Attack, F1 - Debug, ESC - Exit"
            ]
            
            y_offset = 10
            for info in debug_info:
                debug(info, y=y_offset)
                y_offset += 20
        else:
            # Показываем базовые инструкции
            debug("Press F1 for debug info", y=get_config('HEIGHT') - 30)
        
        # Обновление дисплея
        pygame.display.flip()

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

