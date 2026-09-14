import pygame
import os
from collections import deque
from typing import List, Optional, Set, Tuple

from src.core.config_loader import get_config, get_color
from src.world.terrain import TerrainType, TRANSLUCENT_OVERLAY_TYPES
from src.world.map_loader import load_map_from_file
from src.world.camera import Camera
from src.systems.enemy_manager import EnemyManager
from src.systems.projectile_manager import ProjectileManager


class World:
    def __init__(self, map_file: str, width=2000, height=2000):
        """Инициализация игрового мира"""
        self.width = width
        self.height = height

        # Размер тайлов для сетки
        self.tile_size = 32
        self.tiles_x = width // self.tile_size
        self.tiles_y = height // self.tile_size

        # Загружаем карту из файла (земля + опциональный overlay)
        self.terrain_tiles, self.overlay_tiles, self.player_start_x, self.player_start_y = \
            load_map_from_file(map_file)

        # Создаем список препятствий для обратной совместимости
        self.obstacles: List[pygame.Rect] = []
        self.generate_obstacles_from_terrain()

        # Сеточные индексы для O(1) поиска вместо линейного перебора
        # self.obstacles/self.terrain_tiles. Критично для больших карт -
        # на мире 200x200 тайлов (40000 тайлов, ~10к сплошных) линейный
        # перебор на каждый check_collision/get_terrain_at (каждый враг,
        # снаряд и игрок дергают его каждый кадр) был главным узким местом.
        #
        # ВАЖНО: TerrainTile.rect всегда 32x32 (см. src/world/terrain.py) -
        # это не обязательно совпадает с self.tile_size (из config.ini).
        # Индекс собирается по фактическому размеру тайла, а не по конфигу,
        # чтобы check_collision оставался эквивалентен старому линейному
        # перебору self.obstacles независимо от значения tile_size.
        self._collision_grid = (
            self.terrain_tiles[0].rect.width if self.terrain_tiles else self.tile_size
        )
        self._solid_tile_set: Set[Tuple[int, int]] = {
            (tile.x, tile.y) for tile in self.terrain_tiles if tile.is_solid
        }
        self._tile_lookup = {(tile.x, tile.y): tile for tile in self.terrain_tiles}

        # Достижимые от старта игрока тайлы (BFS) - используется спавном
        # врагов (EnemyManager), чтобы не ставить их в изолированные "карманы"
        # ландшафта, куда игрок не может дойти (враг там физически не может
        # встретиться с игроком и выглядит "застрявшим"). None = достижимость
        # не вычислена (стартовая точка сама на непроходимом тайле) -
        # в этом случае ограничение не применяется.
        self._reachable_tiles: Optional[Set[Tuple[int, int]]] = self._compute_reachable_tiles()

        # Камера
        self._camera = Camera()

        # Параметры эффекта прозрачности overlay (когда игрок под верхним слоем)
        self.overlay_alpha_under_player = 120   # альфа когда игрок под тайлом
        self.overlay_alpha_normal = 255         # обычная альфа
        self.player_rect_for_overlay: pygame.Rect = None  # устанавливается из draw()

        # Менеджер врагов. Враги хранятся внутри мира - удобно для save/load
        # и логически правильно (мир = всё что на нём).
        self.enemy_manager = EnemyManager(self)

        # Менеджер летящих снарядов (реальная баллистика стрелкового оружия).
        # Не сериализуется - время жизни пули - доли секунды, терять её при
        # save/load незаметно и не влияет на баланс.
        self.projectile_manager = ProjectileManager(self)

    # --- Камера (делегирует Camera) ----------------------------------------

    @property
    def camera_x(self) -> float:
        return self._camera.x

    @camera_x.setter
    def camera_x(self, value: float):
        self._camera.x = value

    @property
    def camera_y(self) -> float:
        return self._camera.y

    @camera_y.setter
    def camera_y(self, value: float):
        self._camera.y = value

    # --- Генерация и запросы -----------------------------------------------

    def generate_obstacles_from_terrain(self):
        """Генерация препятствий из загруженной terrain карты"""
        for tile in self.terrain_tiles:
            if tile.is_solid:  # Только непроходимые тайлы считаются препятствиями
                self.obstacles.append(tile.rect)
    
    def get_terrain_at(self, x, y):
        """Получить тайл ландшафта в указанной позиции"""
        tile_x = int(x // self.tile_size) * self.tile_size
        tile_y = int(y // self.tile_size) * self.tile_size
        return self._tile_lookup.get((tile_x, tile_y))

    def _compute_reachable_tiles(self) -> Optional[Set[Tuple[int, int]]]:
        """BFS проходимых тайлов от стартовой позиции игрока.

        Возвращает множество (tile_x, tile_y) сплошных-тайловых координат,
        достижимых пешком от точки спавна игрока, в пределах [0, width) x
        [0, height). Если стартовый тайл сам непроходим (не должно
        случаться на валидных картах, но не должно и падать) - возвращает
        None, что означает "ограничение не применяется".
        """
        grid = self._collision_grid
        start = (
            int(self.player_start_x) // grid * grid,
            int(self.player_start_y) // grid * grid,
        )
        if start in self._solid_tile_set:
            return None

        seen = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((grid, 0), (-grid, 0), (0, grid), (0, -grid)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if (nx, ny) in seen or (nx, ny) in self._solid_tile_set:
                    continue
                seen.add((nx, ny))
                queue.append((nx, ny))
        return seen

    def is_position_reachable(self, x, y) -> bool:
        """True если тайл в точке (x, y) достижим пешком от старта игрока.

        Используется спавном врагов (EnemyManager), чтобы не заспавнить
        врага в изолированном "кармане" ландшафта (например, крошечная
        полость внутри горного массива), недостижимом для игрока - там
        враг не может ни дойти до игрока, ни быть атакованным, и выглядит
        "застрявшим". Если достижимость не вычислена (см.
        _compute_reachable_tiles) - ограничение не применяется (True)."""
        if self._reachable_tiles is None:
            return True
        grid = self._collision_grid
        tile = (int(x) // grid * grid, int(y) // grid * grid)
        return tile in self._reachable_tiles

    def get_player_start_position(self):
        """Получить стартовую позицию игрока"""
        return self.player_start_x, self.player_start_y
    
    def update_camera(self, player_x, player_y, screen_width, screen_height):
        """Обновление позиции камеры для следования за игроком"""
        self._camera.follow(player_x, player_y, screen_width, screen_height,
                            self.width, self.height)

    def check_collision(self, rect):
        """Проверка коллизии с препятствиями.

        Смотрит только тайлы сетки, которые пересекает rect (self._solid_tile_set),
        а не весь self.obstacles - эквивалентно старому линейному перебору
        (obstacles - это ровно сплошные тайлы 32x32 по сетке), но O(1) вместо
        O(число сплошных тайлов на карте)."""
        grid = self._collision_grid
        tx0 = rect.left // grid
        tx1 = (rect.right - 1) // grid
        ty0 = rect.top // grid
        ty1 = (rect.bottom - 1) // grid
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if (tx * grid, ty * grid) in self._solid_tile_set:
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

    def draw_overlay(self, screen, player_rect: pygame.Rect = None):
        """Отрисовка верхнего слоя (Z=2) поверх игрока.

        Логика прозрачности зависит от ТИПА overlay-тайла:
          - Тип в TRANSLUCENT_OVERLAY_TYPES (лавки, навесы, кроны деревьев)
            и игрок ПОД тайлом - рисуем полупрозрачно, игрок виден сквозь
            крышу (для интерактива с NPC, торговли и т.п.)
          - Иначе - всегда плотно (HILL_SURFACE прячет игрока полностью,
            не нужно рисовать внутренности холма).
          - EMPTY на overlay - tile.draw() сам пропускает.

        player_rect - в МИРОВЫХ координатах (не экранных).
        """
        if not self.overlay_tiles:
            return

        camera_rect = pygame.Rect(self.camera_x, self.camera_y,
                                  screen.get_width(), screen.get_height())

        for tile in self.overlay_tiles:
            if not camera_rect.colliderect(tile.rect):
                continue

            # Прозрачность только для разрешённых типов И только когда
            # игрок реально пересекает тайл
            is_translucent_type = tile.terrain_type in TRANSLUCENT_OVERLAY_TYPES
            player_under_tile = (
                player_rect is not None
                and tile.rect.colliderect(player_rect)
            )

            if is_translucent_type and player_under_tile:
                # Полупрозрачный рендер - игрок видим сквозь крышу лавки/навеса
                screen_x = tile.x - self.camera_x
                screen_y = tile.y - self.camera_y
                tile_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                color = tile.get_color()
                tile_surf.fill((*color, self.overlay_alpha_under_player))
                screen.blit(tile_surf, (screen_x, screen_y))
            else:
                # Плотная отрисовка (быстрый путь). EMPTY-тайлы tile.draw()
                # сам игнорирует - значит "ореола" вокруг игрока на песке/траве
                # не будет, даже если overlay-сетка пересекает игрока.
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
        """Отрисовка ЗЕМЛЯНОГО слоя мира (без overlay).

        ВНИМАНИЕ: overlay (верхушки холмов и т.п.) нужно рисовать ОТДЕЛЬНО
        после отрисовки игрока через World.draw_overlay(screen, player_rect).
        Это позволяет холму/крыше визуально перекрывать игрока.
        """
        self.draw_background(screen)
        self.draw_obstacles(screen)
        self.draw_minimap(screen, player_x, player_y)