"""
MapLoader - загрузка и парсинг ASCII-карт из файлов.

Single Responsibility: файловый I/O + парсинг символов в TerrainTile.
Не знает про рендер, камеру или мир — только читает текст и создаёт тайлы.
"""
import os

from src.world.terrain import TerrainType, TerrainTile


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

