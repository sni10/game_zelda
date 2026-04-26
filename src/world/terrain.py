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
    
    # Новые типы для механики нор (burrow mechanics)
    BURROW_ENTRANCE = 'O'    # Лаз в нору (вход)
    BURROW_EXIT = 'O'        # Выход из норы
    UNDERGROUND_PATH = 'U'   # Подземная тропинка
    HILL_SURFACE = 'H'       # Поверхность холма (с коровами)
    TRIGGER_BUTTON = 'T'     # Кнопка/переключатель
    NPC_SPAWN = 'N'          # Точка появления NPC
    QUEST_TRIGGER = 'Q'      # Квестовый триггер
    DIALOGUE_ZONE = 'D'      # Зона диалога

    # Просвечиваемые верхние объекты (overlay-only).
    # Под такими тайлами игрок виден полупрозрачно - это для лавок,
    # навесов из пальмовых листьев, крон деревьев и т.п. постройки/декора,
    # под которыми происходит интерактив (NPC, торговля, диалоги).
    # В отличие от HILL_SURFACE, который ВСЕГДА плотный (игрок прячется полностью).
    ROOF_TRANSLUCENT = 'R'   # Просвечиваемая крыша (лавка/навес/палапа)


# Типы overlay-тайлов, которые становятся ПОЛУПРОЗРАЧНЫМИ когда игрок под ними.
# Если тип НЕ в этом наборе - тайл всегда рисуется плотно (например, холм).
TRANSLUCENT_OVERLAY_TYPES = frozenset({
    TerrainType.ROOF_TRANSLUCENT,
})


class TerrainTile:
    """Класс для представления тайла ландшафта"""
    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.rect = pygame.Rect(x, y, 32, 32)  # Размер тайла 32x32
        
        # Свойства тайла
        # HILL_SURFACE на земляном слое - непроходимые "корни/склон" холма.
        # Сама верхушка холма живёт на overlay (Z=2) и через коллизии не идёт.
        self.is_solid = terrain_type in [
            TerrainType.MOUNTAIN, TerrainType.WATER,
            TerrainType.CAVE_WALL, TerrainType.HILL_SURFACE,
        ]
        self.damages_player = terrain_type in [TerrainType.SWAMP, TerrainType.SAND]
        self.slows_player = terrain_type == TerrainType.SAND
        self.damage_amount = 1 if self.damages_player else 0
        self.speed_modifier = 0.5 if self.slows_player else 1.0
        
        # Свойства для новых типов terrain (burrow mechanics)
        self.is_burrow_entrance = terrain_type == TerrainType.BURROW_ENTRANCE
        self.is_burrow_exit = terrain_type == TerrainType.BURROW_EXIT
        self.is_underground_path = terrain_type == TerrainType.UNDERGROUND_PATH
        self.is_hill_surface = terrain_type == TerrainType.HILL_SURFACE
        self.is_trigger = terrain_type in [TerrainType.TRIGGER_BUTTON, TerrainType.QUEST_TRIGGER]
        self.is_interactive = terrain_type in [TerrainType.BURROW_ENTRANCE, TerrainType.BURROW_EXIT, 
                                             TerrainType.TRIGGER_BUTTON, TerrainType.NPC_SPAWN,
                                             TerrainType.QUEST_TRIGGER, TerrainType.DIALOGUE_ZONE]
        
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
            TerrainType.CAVE_SPECIAL: (255, 215, 0),  # Золотой для специальных элементов
            
            # Цвета для новых типов terrain (burrow mechanics)
            TerrainType.BURROW_ENTRANCE: (139, 69, 19),    # Коричневый для входа в нору
            TerrainType.BURROW_EXIT: (160, 82, 45),        # Светло-коричневый для выхода
            TerrainType.UNDERGROUND_PATH: (101, 67, 33),   # Темно-коричневый для подземной тропинки
            TerrainType.HILL_SURFACE: (34, 139, 34),       # Зеленый для поверхности холма
            TerrainType.TRIGGER_BUTTON: (255, 0, 255),     # Магента для кнопки/переключателя
            TerrainType.NPC_SPAWN: (255, 165, 0),          # Оранжевый для точки появления NPC
            TerrainType.QUEST_TRIGGER: (255, 215, 0),      # Золотой для квестового триггера
            TerrainType.DIALOGUE_ZONE: (173, 216, 230),    # Светло-голубой для зоны диалога

            # Цвет крыши лавки/навеса (палевый - как сухие пальмовые листья)
            TerrainType.ROOF_TRANSLUCENT: (160, 120, 60),
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


