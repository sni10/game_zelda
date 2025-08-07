import pygame
from enum import Enum
from src.core.config_loader import get_color


class TerrainType(Enum):
    """Типы ландшафта"""
    EMPTY = '.'      # Пустое пространство (проходимо)
    MOUNTAIN = '#'   # Горы (непроходимо)
    WATER = '~'      # Вода (непроходимо)
    TREE = '^'       # Деревья/кусты (проходимо, декоративные)
    SWAMP = 'M'      # Болото (проходимо, наносит урон)
    SAND = 'S'       # Зыбучие пески (проходимо, замедляет и наносит урон)
    PLAYER_START = '@'  # Стартовая позиция игрока
    CAVE_WALL = 'B'  # Стены пещеры (непроходимо)
    CAVE_SPECIAL = '+'  # Специальные элементы пещеры (проходимо)


class TerrainTile:
    """Класс для представления тайла ландшафта"""
    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.rect = pygame.Rect(x, y, 32, 32)  # Размер тайла 32x32
        
        # Свойства тайла
        self.is_solid = terrain_type in [TerrainType.MOUNTAIN, TerrainType.WATER, TerrainType.CAVE_WALL]
        self.damages_player = terrain_type in [TerrainType.SWAMP, TerrainType.SAND]
        self.slows_player = terrain_type == TerrainType.SAND
        self.damage_amount = 1 if self.damages_player else 0
        self.speed_modifier = 0.5 if self.slows_player else 1.0
        
    def get_color(self):
        """Получить цвет для отрисовки тайла"""
        color_map = {
            TerrainType.EMPTY: get_color('DARK_GREEN'),
            TerrainType.MOUNTAIN: get_color('DARK_GRAY'),
            TerrainType.WATER: (0, 100, 200),  # Синий
            TerrainType.TREE: (0, 150, 0),     # Темно-зеленый
            TerrainType.SWAMP: (100, 50, 0),   # Коричнево-зеленый
            TerrainType.SAND: (200, 180, 100), # Песочный
            TerrainType.PLAYER_START: get_color('DARK_GREEN'),
            TerrainType.CAVE_WALL: (101, 67, 33),  # Темно-коричневый для стен пещеры
            TerrainType.CAVE_SPECIAL: (255, 215, 0)  # Золотой для специальных элементов
        }
        return color_map.get(self.terrain_type, get_color('WHITE'))
    
    def draw(self, screen, camera_x, camera_y):
        """Отрисовка тайла"""
        if self.terrain_type == TerrainType.EMPTY:
            return  # Пустые тайлы не рисуем (фон уже нарисован)
            
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Рисуем тайл только если он видим на экране
        if -32 <= screen_x <= screen.get_width() and -32 <= screen_y <= screen.get_height():
            color = self.get_color()
            pygame.draw.rect(screen, color, (screen_x, screen_y, 32, 32))
            
            # Добавляем границу для некоторых типов
            if self.terrain_type in [TerrainType.MOUNTAIN, TerrainType.WATER]:
                pygame.draw.rect(screen, get_color('BLACK'), (screen_x, screen_y, 32, 32), 1)


def load_map_from_file(filename):
    """Загрузка карты из ASCII файла"""
    terrain_tiles = []
    player_start_x, player_start_y = 1000, 1000  # По умолчанию в центре
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Пропускаем строки с комментариями (начинающиеся с "# ")
        map_lines = []
        for line in lines:
            line = line.rstrip('\n\r')
            # Комментарии начинаются с "# " (решетка и пробел)
            # Строки карты могут начинаться с "#" но это символ границы мира
            if not line.startswith('# ') and line.strip():
                map_lines.append(line)
        
        
        # Парсим карту
        for y, line in enumerate(map_lines):
            for x, char in enumerate(line):
                tile_x = x * 32
                tile_y = y * 32
                
                try:
                    terrain_type = TerrainType(char)
                    
                    # Запоминаем стартовую позицию игрока
                    if terrain_type == TerrainType.PLAYER_START:
                        player_start_x = tile_x + 16  # Центр тайла
                        player_start_y = tile_y + 16
                        terrain_type = TerrainType.EMPTY  # Заменяем на пустое пространство
                    
                    terrain_tiles.append(TerrainTile(tile_x, tile_y, terrain_type))
                    
                except ValueError:
                    # Неизвестный символ - считаем пустым пространством
                    terrain_tiles.append(TerrainTile(tile_x, tile_y, TerrainType.EMPTY))
    
    except FileNotFoundError:
        print(f"Файл карты {filename} не найден!")
        return [], 1000, 1000
    
    
    return terrain_tiles, player_start_x, player_start_y