"""
Abstract Factory Pattern для создания различных типов миров
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from src.core.ecs.entity import Entity, EntityManager
from src.core.ecs.component import (
    PositionComponent, WorldComponent, TunnelComponent, 
    PortalComponent, RenderLayerComponent, LoadingScreenComponent
)
from src.rendering.layer_renderer import LayeredWorld


class WorldFactory(ABC):
    """Абстрактная фабрика для создания различных типов миров"""
    
    def __init__(self, entity_manager: EntityManager):
        self.entity_manager = entity_manager
        
    @abstractmethod
    def create_world(self, world_id: str, size: Tuple[int, int]) -> LayeredWorld:
        """Создать мир"""
        pass
    
    @abstractmethod
    def create_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности для мира"""
        pass
    
    @abstractmethod
    def create_portals(self, world: LayeredWorld) -> List[Entity]:
        """Создать порталы для мира"""
        pass
    
    @abstractmethod
    def get_world_type(self) -> str:
        """Получить тип мира"""
        pass
    
    def create_complete_world(self, world_id: str, size: Tuple[int, int]) -> Tuple[LayeredWorld, List[Entity]]:
        """Создать полный мир со всеми сущностями"""
        # Создаем мир
        world = self.create_world(world_id, size)
        
        # Создаем все сущности
        entities = []
        entities.extend(self.create_entities(world))
        entities.extend(self.create_portals(world))
        
        return world, entities


class MainWorldFactory(WorldFactory):
    """Фабрика для основного мира"""
    
    def get_world_type(self) -> str:
        return "main"
    
    def create_world(self, world_id: str, size: Tuple[int, int]) -> LayeredWorld:
        """Создать основной мир"""
        width, height = size
        
        # Создаем поверхностную карту (простая для начала)
        surface_map = self._create_surface_map(width, height)
        
        # Основной мир может не иметь подземных тоннелей
        underground_map = None
        
        world = LayeredWorld(world_id, surface_map, underground_map)
        return world
    
    def create_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности для основного мира"""
        entities = []
        
        # Создаем базовые элементы ландшафта
        entities.extend(self._create_terrain_entities(world))
        
        # Создаем NPC (торговцы, квестодатели)
        entities.extend(self._create_npcs(world))
        
        return entities
    
    def create_portals(self, world: LayeredWorld) -> List[Entity]:
        """Создать порталы для основного мира"""
        portals = []
        
        # Портал в мир-пещеру
        cave_portal = self._create_portal(
            position=(500, 500),
            target_world="cave_world",
            target_position=(100, 100),
            target_z=0
        )
        portals.append(cave_portal)
        
        # Портал во второй обычный мир с пещерами
        second_world_portal = self._create_portal(
            position=(200, 300),
            target_world="second_world",
            target_position=(100, 100),
            target_z=0
        )
        portals.append(second_world_portal)
        
        return portals
    
    def _create_surface_map(self, width: int, height: int) -> List[List[str]]:
        """Создать поверхностную карту"""
        # Простая карта с травой и препятствиями
        tile_width = width // 32
        tile_height = height // 32
        
        surface_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                # Границы мира - горы
                if x == 0 or x == tile_width - 1 or y == 0 or y == tile_height - 1:
                    row.append('#')  # Горы
                # Несколько случайных препятствий
                elif (x + y) % 10 == 0:
                    row.append('^')  # Деревья
                else:
                    row.append('.')  # Трава
            surface_map.append(row)
        
        return surface_map
    
    def _create_terrain_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности ландшафта"""
        entities = []
        
        # Пока создаем простые сущности для демонстрации
        # В будущем это будет загружаться из карт
        
        return entities
    
    def _create_npcs(self, world: LayeredWorld) -> List[Entity]:
        """Создать NPC для основного мира"""
        npcs = []
        
        # Торговец
        merchant = self.entity_manager.create_entity()
        merchant.add_component(PositionComponent(300, 300, 0, world.world_id))
        merchant.add_component(RenderLayerComponent(0))
        npcs.append(merchant)
        
        return npcs
    
    def _create_portal(self, position: Tuple[int, int], target_world: str, 
                      target_position: Tuple[int, int], target_z: int = 0) -> Entity:
        """Создать портал"""
        portal = self.entity_manager.create_entity()
        portal.add_component(PositionComponent(position[0], position[1], 0))
        portal.add_component(PortalComponent(target_world, target_position, target_z))
        portal.add_component(RenderLayerComponent(0))
        return portal


class CaveWorldFactory(WorldFactory):
    """Фабрика для мира-пещеры с тоннелями"""
    
    def get_world_type(self) -> str:
        return "cave"
    
    def create_world(self, world_id: str, size: Tuple[int, int]) -> LayeredWorld:
        """Создать мир-пещеру с тоннелями"""
        width, height = size
        
        # Создаем поверхностную карту
        surface_map = self._create_cave_surface_map(width, height)
        
        # Создаем подземную карту с тоннелями
        underground_map = self._create_underground_map(width, height)
        
        world = LayeredWorld(world_id, surface_map, underground_map)
        return world
    
    def create_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности для мира-пещеры"""
        entities = []
        
        # Создаем тоннели
        entities.extend(self._create_tunnels(world))
        
        # Создаем элементы ландшафта
        entities.extend(self._create_cave_terrain(world))
        
        return entities
    
    def create_portals(self, world: LayeredWorld) -> List[Entity]:
        """Создать порталы для мира-пещеры"""
        portals = []
        
        # Портал обратно в основной мир
        return_portal = self._create_portal(
            position=(100, 100),
            target_world="main_world",
            target_position=(500, 500),
            target_z=0
        )
        portals.append(return_portal)
        
        return portals
    
    def _create_cave_surface_map(self, width: int, height: int) -> List[List[str]]:
        """Создать поверхностную карту пещеры"""
        tile_width = width // 32
        tile_height = height // 32
        
        surface_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                # Границы - горы
                if x == 0 or x == tile_width - 1 or y == 0 or y == tile_height - 1:
                    row.append('#')  # Горы
                # Входы в тоннели в определенных местах
                elif self._is_tunnel_entrance(x, y, tile_width, tile_height):
                    row.append('T')  # Вход в тоннель (специальный символ)
                else:
                    row.append('.')  # Травяные поля
            surface_map.append(row)
        
        return surface_map
    
    def _create_underground_map(self, width: int, height: int) -> List[List[str]]:
        """Создать подземную карту с тоннелями"""
        tile_width = width // 32
        tile_height = height // 32
        
        underground_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                if self._is_tunnel_path(x, y, tile_width, tile_height):
                    row.append('P')  # Путь тоннеля
                elif self._is_tunnel_wall(x, y, tile_width, tile_height):
                    row.append('W')  # Стена тоннеля
                else:
                    row.append('.')  # Пустое подземное пространство
            underground_map.append(row)
        
        return underground_map
    
    def _is_tunnel_entrance(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция входом в тоннель"""
        # Три входа в тоннели в разных местах
        entrances = [
            (width // 4, height // 2),      # Короткий тоннель
            (width // 2, height // 3),      # Средний тоннель
            (3 * width // 4, height // 2)   # Длинный тоннель
        ]
        return (x, y) in entrances
    
    def _is_tunnel_path(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция путем тоннеля"""
        # Создаем три тоннеля разной длины
        
        # Короткий тоннель (2 клетки)
        if (width // 4 <= x <= width // 4 + 1 and 
            height // 2 - 1 <= y <= height // 2):
            return True
            
        # Средний тоннель (3-4 клетки)
        if (width // 2 <= x <= width // 2 + 3 and 
            height // 3 - 1 <= y <= height // 3):
            return True
            
        # Длинный тоннель (5 клеток)
        if (3 * width // 4 <= x <= 3 * width // 4 + 4 and 
            height // 2 - 1 <= y <= height // 2):
            return True
            
        return False
    
    def _is_tunnel_wall(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция стеной тоннеля"""
        # Стены вокруг путей тоннелей
        # Упрощенная логика - в реальности будет более сложная
        
        # Проверяем области вокруг тоннелей
        tunnel_areas = [
            (width // 4 - 1, width // 4 + 2, height // 2 - 2, height // 2 + 1),
            (width // 2 - 1, width // 2 + 4, height // 3 - 2, height // 3 + 1),
            (3 * width // 4 - 1, 3 * width // 4 + 5, height // 2 - 2, height // 2 + 1)
        ]
        
        for x1, x2, y1, y2 in tunnel_areas:
            if x1 <= x <= x2 and y1 <= y <= y2:
                # Если это не путь тоннеля, то это стена
                if not self._is_tunnel_path(x, y, width, height):
                    return True
        
        return False
    
    def _create_tunnels(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности тоннелей"""
        tunnels = []
        
        # Короткий тоннель
        short_tunnel = self.entity_manager.create_entity()
        short_tunnel.add_component(TunnelComponent(
            entrance_pos=(128, 256),  # 4*32, 8*32
            exit_pos=(160, 256),      # 5*32, 8*32
            length=2
        ))
        short_tunnel.add_component(PositionComponent(128, 256, -1, world.world_id))
        short_tunnel.add_component(RenderLayerComponent(-1))
        tunnels.append(short_tunnel)
        
        # Средний тоннель
        medium_tunnel = self.entity_manager.create_entity()
        medium_tunnel.add_component(TunnelComponent(
            entrance_pos=(256, 170),  # 8*32, 5.3*32
            exit_pos=(352, 170),      # 11*32, 5.3*32
            length=3
        ))
        medium_tunnel.add_component(PositionComponent(256, 170, -1, world.world_id))
        medium_tunnel.add_component(RenderLayerComponent(-1))
        tunnels.append(medium_tunnel)
        
        # Длинный тоннель
        long_tunnel = self.entity_manager.create_entity()
        long_tunnel.add_component(TunnelComponent(
            entrance_pos=(384, 256),  # 12*32, 8*32
            exit_pos=(544, 256),      # 17*32, 8*32
            length=5
        ))
        long_tunnel.add_component(PositionComponent(384, 256, -1, world.world_id))
        long_tunnel.add_component(RenderLayerComponent(-1))
        tunnels.append(long_tunnel)
        
        return tunnels
    
    def _create_cave_terrain(self, world: LayeredWorld) -> List[Entity]:
        """Создать элементы ландшафта пещеры"""
        terrain = []
        
        # Пока простая реализация
        # В будущем будет загружаться из карт
        
        return terrain
    
    def _create_portal(self, position: Tuple[int, int], target_world: str, 
                      target_position: Tuple[int, int], target_z: int = 0) -> Entity:
        """Создать портал"""
        portal = self.entity_manager.create_entity()
        portal.add_component(PositionComponent(position[0], position[1], 0))
        portal.add_component(PortalComponent(target_world, target_position, target_z))
        portal.add_component(RenderLayerComponent(0))
        return portal


class UndergroundWorldFactory(WorldFactory):
    """Фабрика для подземного мира"""
    
    def get_world_type(self) -> str:
        return "underground"
    
    def create_world(self, world_id: str, size: Tuple[int, int]) -> LayeredWorld:
        """Создать подземный мир"""
        width, height = size
        
        # Подземный мир существует только на Z=-1
        surface_map = self._create_empty_surface(width, height)
        underground_map = self._create_underground_caverns(width, height)
        
        world = LayeredWorld(world_id, surface_map, underground_map)
        return world
    
    def create_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности для подземного мира"""
        entities = []
        
        # Лавовые озера, особые враги, сокровища
        entities.extend(self._create_underground_features(world))
        
        return entities
    
    def create_portals(self, world: LayeredWorld) -> List[Entity]:
        """Создать порталы для подземного мира"""
        portals = []
        
        # Портал обратно на поверхность
        return_portal = self._create_portal(
            position=(200, 200),
            target_world="main_world",
            target_position=(600, 600),
            target_z=0
        )
        portals.append(return_portal)
        
        return portals
    
    def _create_empty_surface(self, width: int, height: int) -> List[List[str]]:
        """Создать пустую поверхность"""
        tile_width = width // 32
        tile_height = height // 32
        
        return [['.' for _ in range(tile_width)] for _ in range(tile_height)]
    
    def _create_underground_caverns(self, width: int, height: int) -> List[List[str]]:
        """Создать подземные пещеры"""
        tile_width = width // 32
        tile_height = height // 32
        
        underground_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                # Создаем пещерную структуру
                if x == 0 or x == tile_width - 1 or y == 0 or y == tile_height - 1:
                    row.append('#')  # Стены пещеры
                elif (x + y) % 7 == 0:
                    row.append('L')  # Лава (специальный символ)
                elif (x * y) % 11 == 0:
                    row.append('#')  # Столбы/препятствия
                else:
                    row.append('.')  # Проходимые области
            underground_map.append(row)
        
        return underground_map
    
    def _create_underground_features(self, world: LayeredWorld) -> List[Entity]:
        """Создать особенности подземного мира"""
        features = []
        
        # Лавовые озера, кристаллы, особые враги
        # Пока простая реализация
        
        return features
    
    def _create_portal(self, position: Tuple[int, int], target_world: str, 
                      target_position: Tuple[int, int], target_z: int = 0) -> Entity:
        """Создать портал"""
        portal = self.entity_manager.create_entity()
        portal.add_component(PositionComponent(position[0], position[1], -1))  # Подземный портал
        portal.add_component(PortalComponent(target_world, target_position, target_z))
        portal.add_component(RenderLayerComponent(-1))
        return portal




class SecondWorldFactory(WorldFactory):
    """Фабрика для второго обычного мира с несколькими пещерами"""
    
    def get_world_type(self) -> str:
        return "second"
    
    def create_world(self, world_id: str, size: Tuple[int, int]) -> LayeredWorld:
        """Создать второй обычный мир с пещерами"""
        width, height = size
        
        # Создаем поверхностную карту
        surface_map = self._create_second_world_surface(width, height)
        
        # Создаем подземную карту с несколькими пещерами
        underground_map = self._create_caves_map(width, height)
        
        world = LayeredWorld(world_id, surface_map, underground_map)
        return world
    
    def create_entities(self, world: LayeredWorld) -> List[Entity]:
        """Создать сущности для второго мира"""
        entities = []
        
        # Создаем входы в пещеры
        entities.extend(self._create_cave_entrances(world))
        
        # Создаем элементы ландшафта
        entities.extend(self._create_second_world_terrain(world))
        
        return entities
    
    def create_portals(self, world: LayeredWorld) -> List[Entity]:
        """Создать порталы для второго мира"""
        portals = []
        
        # Портал обратно в основной мир
        return_portal = self._create_portal(
            position=(100, 100),
            target_world="main_world",
            target_position=(400, 400),
            target_z=0
        )
        portals.append(return_portal)
        
        return portals
    
    def _create_second_world_surface(self, width: int, height: int) -> List[List[str]]:
        """Создать поверхностную карту второго мира"""
        tile_width = width // 32
        tile_height = height // 32
        
        surface_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                # Границы мира - горы
                if x == 0 or x == tile_width - 1 or y == 0 or y == tile_height - 1:
                    row.append('#')  # Горы
                # Входы в пещеры в разных местах
                elif self._is_cave_entrance(x, y, tile_width, tile_height):
                    row.append('C')  # Вход в пещеру (специальный символ)
                # Несколько деревьев и препятствий
                elif (x + y) % 8 == 0:
                    row.append('^')  # Деревья
                # Несколько водоемов
                elif (x * 2 + y) % 15 == 0:
                    row.append('~')  # Вода
                else:
                    row.append('.')  # Обычная трава
            surface_map.append(row)
        
        return surface_map
    
    def _create_caves_map(self, width: int, height: int) -> List[List[str]]:
        """Создать подземную карту с пещерами"""
        tile_width = width // 32
        tile_height = height // 32
        
        underground_map = []
        for y in range(tile_height):
            row = []
            for x in range(tile_width):
                if self._is_cave_path(x, y, tile_width, tile_height):
                    row.append('P')  # Путь в пещере
                elif self._is_cave_wall(x, y, tile_width, tile_height):
                    row.append('W')  # Стена пещеры
                else:
                    row.append('.')  # Пустое подземное пространство
            underground_map.append(row)
        
        return underground_map
    
    def _is_cave_entrance(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция входом в пещеру"""
        # Несколько входов в пещеры в разных местах
        entrances = [
            (width // 6, height // 3),      # Первая пещера
            (width // 2, height // 4),      # Вторая пещера
            (4 * width // 5, height // 2),  # Третья пещера
            (width // 3, 3 * height // 4)   # Четвертая пещера
        ]
        return (x, y) in entrances
    
    def _is_cave_path(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция путем в пещере"""
        # Создаем несколько пещер разного размера
        
        # Первая пещера (маленькая)
        if (width // 6 - 1 <= x <= width // 6 + 2 and 
            height // 3 - 1 <= y <= height // 3 + 1):
            return True
            
        # Вторая пещера (средняя)
        if (width // 2 - 2 <= x <= width // 2 + 3 and 
            height // 4 - 1 <= y <= height // 4 + 2):
            return True
            
        # Третья пещера (большая)
        if (4 * width // 5 - 3 <= x <= 4 * width // 5 + 4 and 
            height // 2 - 2 <= y <= height // 2 + 2):
            return True
            
        # Четвертая пещера (длинная)
        if (width // 3 - 1 <= x <= width // 3 + 5 and 
            3 * height // 4 - 1 <= y <= 3 * height // 4 + 1):
            return True
            
        return False
    
    def _is_cave_wall(self, x: int, y: int, width: int, height: int) -> bool:
        """Определить, является ли позиция стеной пещеры"""
        # Стены вокруг путей пещер
        cave_areas = [
            (width // 6 - 2, width // 6 + 3, height // 3 - 2, height // 3 + 2),
            (width // 2 - 3, width // 2 + 4, height // 4 - 2, height // 4 + 3),
            (4 * width // 5 - 4, 4 * width // 5 + 5, height // 2 - 3, height // 2 + 3),
            (width // 3 - 2, width // 3 + 6, 3 * height // 4 - 2, 3 * height // 4 + 2)
        ]
        
        for x1, x2, y1, y2 in cave_areas:
            if x1 <= x <= x2 and y1 <= y <= y2:
                # Если это не путь пещеры, то это стена
                if not self._is_cave_path(x, y, width, height):
                    return True
        
        return False
    
    def _create_cave_entrances(self, world: LayeredWorld) -> List[Entity]:
        """Создать входы в пещеры"""
        entrances = []
        
        # Создаем входы для каждой пещеры
        cave_positions = [
            (96, 64),    # 3*32, 2*32 - первая пещера
            (256, 96),   # 8*32, 3*32 - вторая пещера
            (512, 256),  # 16*32, 8*32 - третья пещера
            (160, 384)   # 5*32, 12*32 - четвертая пещера
        ]
        
        for i, pos in enumerate(cave_positions):
            entrance = self.entity_manager.create_entity()
            entrance.add_component(PositionComponent(pos[0], pos[1], 0, world.world_id))
            entrance.add_component(RenderLayerComponent(0))
            entrances.append(entrance)
        
        return entrances
    
    def _create_second_world_terrain(self, world: LayeredWorld) -> List[Entity]:
        """Создать элементы ландшафта второго мира"""
        terrain = []
        
        # Пока простая реализация
        # В будущем будет загружаться из карт
        
        return terrain
    
    def _create_portal(self, position: Tuple[int, int], target_world: str, 
                      target_position: Tuple[int, int], target_z: int = 0) -> Entity:
        """Создать портал"""
        portal = self.entity_manager.create_entity()
        portal.add_component(PositionComponent(position[0], position[1], 0))
        portal.add_component(PortalComponent(target_world, target_position, target_z))
        portal.add_component(RenderLayerComponent(0))
        return portal


class WorldFactoryRegistry:
    """Реестр фабрик миров"""
    
    def __init__(self, entity_manager: EntityManager):
        self.entity_manager = entity_manager
        self.factories: Dict[str, WorldFactory] = {}
        self._register_default_factories()
    
    def _register_default_factories(self):
        """Зарегистрировать стандартные фабрики"""
        self.register_factory("main", MainWorldFactory(self.entity_manager))
        self.register_factory("cave", CaveWorldFactory(self.entity_manager))
        self.register_factory("underground", UndergroundWorldFactory(self.entity_manager))
        self.register_factory("second", SecondWorldFactory(self.entity_manager))
    
    def register_factory(self, world_type: str, factory: WorldFactory):
        """Зарегистрировать фабрику"""
        self.factories[world_type] = factory
    
    def get_factory(self, world_type: str) -> Optional[WorldFactory]:
        """Получить фабрику по типу мира"""
        return self.factories.get(world_type)
    
    def create_world(self, world_type: str, world_id: str, 
                    size: Tuple[int, int]) -> Optional[Tuple[LayeredWorld, List[Entity]]]:
        """Создать мир указанного типа"""
        factory = self.get_factory(world_type)
        if factory:
            return factory.create_complete_world(world_id, size)
        return None
    
    def get_available_world_types(self) -> List[str]:
        """Получить список доступных типов миров"""
        return list(self.factories.keys())