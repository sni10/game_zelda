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


OVERLAY_SUFFIX = '_overlay'  # main_world.txt -> main_world_overlay.txt


def _parse_map_lines(map_lines):
    """Парсинг ASCII-строк карты в список TerrainTile.

    Возвращает (tiles, player_start_x, player_start_y).
    Если PLAYER_START в блоке нет, координаты None.

    ВАЖНО: файлы карт должны быть чистым ASCII без комментариев.
    Пустые строки пропускаются (для совместимости с разными редакторами).
    """
    tiles = []
    player_start_x, player_start_y = None, None

    # Пропускаем только пустые строки (карты должны быть чистым ASCII)
    grid = [ln for ln in map_lines if ln.strip()]

    for y, line in enumerate(grid):
        for x, char in enumerate(line):
            tile_x = x * 32
            tile_y = y * 32

            try:
                terrain_type = TerrainType(char)

                if terrain_type == TerrainType.PLAYER_START:
                    player_start_x = tile_x + 16
                    player_start_y = tile_y + 16
                    terrain_type = TerrainType.EMPTY

                tiles.append(TerrainTile(tile_x, tile_y, terrain_type))

            except ValueError:
                # Неизвестный символ - считаем пустым пространством
                tiles.append(TerrainTile(tile_x, tile_y, TerrainType.EMPTY))

    return tiles, player_start_x, player_start_y


def _read_map_file(filename):
    """Прочитать ASCII-карту из файла. Возвращает список строк или None."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [ln.rstrip('\n\r') for ln in f.readlines()]
    except FileNotFoundError:
        return None


def _overlay_path_for(ground_path):
    """Получить путь к overlay-файлу рядом с земляной картой.

    Пример: data/main_world.txt -> data/main_world_overlay.txt
    """
    import os
    base, ext = os.path.splitext(ground_path)
    return f"{base}{OVERLAY_SUFFIX}{ext}"


def load_map_from_file(filename):
    """Загрузка карты из ASCII файла.

    Слои разделены на отдельные файлы:
      - <name>.txt          - земляной слой (Z=1), коллизии и геймплей
      - <name>_overlay.txt  - верхний слой (Z=2), рисуется поверх игрока
                              (опционально - если файла нет, overlay пустой)

    Файлы должны содержать только ASCII-сетку тайлов, БЕЗ комментариев.

    Возвращает (ground_tiles, overlay_tiles, player_start_x, player_start_y).
    """
    ground_lines = _read_map_file(filename)
    if ground_lines is None:
        print(f"Файл карты {filename} не найден!")
        return [], [], 1000, 1000

    ground_tiles, psx, psy = _parse_map_lines(ground_lines)
    player_start_x = psx if psx is not None else 1000
    player_start_y = psy if psy is not None else 1000

    # Опциональный overlay-слой из соседнего файла
    overlay_tiles = []
    overlay_lines = _read_map_file(_overlay_path_for(filename))
    if overlay_lines is not None:
        overlay_tiles, _, _ = _parse_map_lines(overlay_lines)

    return ground_tiles, overlay_tiles, player_start_x, player_start_y
