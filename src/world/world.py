import pygame
import os
from src.core.config_loader import get_config, get_color
from src.world.terrain import load_map_from_file, TerrainType


class World:
    def __init__(self, width=2000, height=2000):
        """Инициализация игрового мира"""
        self.width = width
        self.height = height
        
        # Размер тайлов для сетки
        self.tile_size = 32
        self.tiles_x = width // self.tile_size
        self.tiles_y = height // self.tile_size
        
        # Загружаем карту из файла
        map_file = os.path.join('data', 'world_map.txt')
        self.terrain_tiles, self.player_start_x, self.player_start_y = load_map_from_file(map_file)
        
        # Создаем список препятствий для обратной совместимости
        self.obstacles = []
        self.generate_obstacles_from_terrain()
        
        # Камера
        self.camera_x = 0
        self.camera_y = 0
        
    def generate_obstacles_from_terrain(self):
        """Генерация препятствий из загруженной terrain карты"""
        for tile in self.terrain_tiles:
            if tile.is_solid:  # Только непроходимые тайлы считаются препятствиями
                self.obstacles.append(tile.rect)
    
    def get_terrain_at(self, x, y):
        """Получить тайл ландшафта в указанной позиции"""
        tile_x = int(x // self.tile_size) * self.tile_size
        tile_y = int(y // self.tile_size) * self.tile_size
        
        for tile in self.terrain_tiles:
            if tile.x == tile_x and tile.y == tile_y:
                return tile
        return None
    
    def get_player_start_position(self):
        """Получить стартовую позицию игрока"""
        return self.player_start_x, self.player_start_y
    
    def update_camera(self, player_x, player_y, screen_width, screen_height):
        """Обновление позиции камеры для следования за игроком"""
        # Центрируем камеру на игроке
        self.camera_x = player_x - screen_width // 2
        self.camera_y = player_y - screen_height // 2
        
        # Ограничиваем камеру границами мира
        self.camera_x = max(0, min(self.camera_x, self.width - screen_width))
        self.camera_y = max(0, min(self.camera_y, self.height - screen_height))
    
    def check_collision(self, rect):
        """Проверка коллизии с препятствиями"""
        for obstacle in self.obstacles:
            if rect.colliderect(obstacle):
                return True
        return False
    
    def get_visible_obstacles(self, screen_width, screen_height):
        """Получить препятствия, видимые на экране"""
        visible_obstacles = []
        camera_rect = pygame.Rect(self.camera_x, self.camera_y, screen_width, screen_height)
        
        for obstacle in self.obstacles:
            if camera_rect.colliderect(obstacle):
                visible_obstacles.append(obstacle)
        
        return visible_obstacles
    
    def draw_background(self, screen):
        """Отрисовка фона мира"""
        screen.fill(get_color('DARK_GREEN'))
        
        # Рисуем сетку для лучшей ориентации
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Вертикальные линии сетки
        start_x = int(self.camera_x // self.tile_size) * self.tile_size
        for x in range(start_x, start_x + screen_width + self.tile_size, self.tile_size):
            screen_x = x - self.camera_x
            if 0 <= screen_x <= screen_width:
                pygame.draw.line(screen, (0, 80, 0), (screen_x, 0), (screen_x, screen_height), 1)
        
        # Горизонтальные линии сетки
        start_y = int(self.camera_y // self.tile_size) * self.tile_size
        for y in range(start_y, start_y + screen_height + self.tile_size, self.tile_size):
            screen_y = y - self.camera_y
            if 0 <= screen_y <= screen_height:
                pygame.draw.line(screen, (0, 80, 0), (0, screen_y), (screen_width, screen_y), 1)
    
    def draw_obstacles(self, screen):
        """Отрисовка ландшафта"""
        # Отрисовываем все видимые тайлы ландшафта
        camera_rect = pygame.Rect(self.camera_x, self.camera_y, screen.get_width(), screen.get_height())
        
        for tile in self.terrain_tiles:
            if camera_rect.colliderect(tile.rect):
                tile.draw(screen, self.camera_x, self.camera_y)
    
    def draw_minimap(self, screen, player_x, player_y):
        """Отрисовка мини-карты в углу экрана"""
        minimap_size = 150
        minimap_x = screen.get_width() - minimap_size - 10
        minimap_y = 10
        
        # Фон мини-карты
        pygame.draw.rect(screen, get_color('BLACK'), (minimap_x, minimap_y, minimap_size, minimap_size))
        pygame.draw.rect(screen, get_color('WHITE'), (minimap_x, minimap_y, minimap_size, minimap_size), 2)
        
        # Масштаб мини-карты
        scale_x = minimap_size / self.width
        scale_y = minimap_size / self.height
        
        # Рисуем препятствия на мини-карте
        for obstacle in self.obstacles[::10]:  # Показываем каждое 10-е препятствие для производительности
            mini_x = minimap_x + int(obstacle.x * scale_x)
            mini_y = minimap_y + int(obstacle.y * scale_y)
            mini_w = max(1, int(obstacle.width * scale_x))
            mini_h = max(1, int(obstacle.height * scale_y))
            pygame.draw.rect(screen, get_color('GRAY'), (mini_x, mini_y, mini_w, mini_h))
        
        # Рисуем игрока на мини-карте
        player_mini_x = minimap_x + int(player_x * scale_x)
        player_mini_y = minimap_y + int(player_y * scale_y)
        pygame.draw.circle(screen, get_color('RED'), (player_mini_x, player_mini_y), 3)
        
        # Рисуем область видимости камеры
        camera_mini_x = minimap_x + int(self.camera_x * scale_x)
        camera_mini_y = minimap_y + int(self.camera_y * scale_y)
        camera_mini_w = int(screen.get_width() * scale_x)
        camera_mini_h = int(screen.get_height() * scale_y)
        pygame.draw.rect(screen, get_color('YELLOW'), (camera_mini_x, camera_mini_y, camera_mini_w, camera_mini_h), 1)
    
    def draw(self, screen, player_x, player_y):
        """Отрисовка всего мира"""
        self.draw_background(screen)
        self.draw_obstacles(screen)
        self.draw_minimap(screen, player_x, player_y)