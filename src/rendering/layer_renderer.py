"""
LayerRenderer - система многослойного рендеринга для Z-координат
"""
import pygame
from typing import Dict, List, Set, Tuple
from src.core.ecs.system import RenderSystem
from src.core.ecs.entity import Entity, EntityManager
from src.core.ecs.component import PositionComponent, RenderLayerComponent
from .layer_strategies import LayerRenderStrategy, StrategyFactory


class LayerRenderer(RenderSystem):
    """Система рендеринга по слоям с поддержкой Z-координат"""
    
    def __init__(self, entity_manager: EntityManager, screen: pygame.Surface):
        super().__init__(entity_manager, screen)
        self.priority = 5  # Высокий приоритет для рендеринга
        
        # Стратегии рендеринга для разных Z-уровней
        self.strategies: Dict[int, LayerRenderStrategy] = {}
        self.overlay_strategy: LayerRenderStrategy = None
        
        # Текущий Z-уровень игрока для эффектов перекрытия
        self.player_z_level = 0
        
        # Кэш сущностей по Z-уровням для оптимизации
        self.entities_by_z_level: Dict[int, Set[Entity]] = {}
        self.cache_dirty = True
        
        # Инициализируем стратегии
        self._initialize_strategies()
        
    def _initialize_strategies(self):
        """Инициализировать стратегии рендеринга"""
        # Создаем стратегии для каждого Z-уровня
        for z_level in [-1, 0, 1]:
            self.strategies[z_level] = StrategyFactory.create_strategy(z_level)
            
        # Создаем стратегию перекрытия
        self.overlay_strategy = StrategyFactory.create_strategy(
            0, is_overlay=True, player_z_level=self.player_z_level
        )
        
    def update(self, dt: float):
        """Обновление системы рендеринга"""
        # Обновляем кэш сущностей если необходимо
        if self.cache_dirty:
            self._update_entity_cache()
            
        # Очищаем экран
        self.screen.fill((0, 0, 0))  # Черный фон
        
        # Рендерим все слои в правильном порядке
        self._render_all_layers()
        
    def _update_entity_cache(self):
        """Обновить кэш сущностей по Z-уровням"""
        self.entities_by_z_level.clear()
        
        # Получаем все сущности с компонентами позиции и рендеринга
        entities = self.get_entities()
        
        for entity in entities:
            pos_comp = entity.get_component(PositionComponent)
            if pos_comp:
                z_level = pos_comp.z
                if z_level not in self.entities_by_z_level:
                    self.entities_by_z_level[z_level] = set()
                self.entities_by_z_level[z_level].add(entity)
                
        self.cache_dirty = False
        
    def _render_all_layers(self):
        """Отрендерить все слои в правильном порядке"""
        camera_offset = (self.camera_x, self.camera_y)
        
        # Получаем все стратегии в порядке приоритета
        all_strategies = StrategyFactory.get_all_strategies(self.player_z_level)
        
        # Рендерим каждый слой
        for strategy in all_strategies:
            self._render_layer_with_strategy(strategy, camera_offset)
            
    def _render_layer_with_strategy(self, strategy: LayerRenderStrategy, 
                                  camera_offset: Tuple[float, float]):
        """Отрендерить слой с использованием указанной стратегии"""
        # Определяем, какие сущности нужно рендерить этой стратегией
        entities_to_render = self._get_entities_for_strategy(strategy)
        
        # Фильтруем видимые сущности
        visible_entities = self._filter_visible_entities(entities_to_render, camera_offset)
        
        # Рендерим каждую сущность
        for entity in visible_entities:
            strategy.render(entity, self.screen, camera_offset)
            
    def _get_entities_for_strategy(self, strategy: LayerRenderStrategy) -> Set[Entity]:
        """Получить сущности для рендеринга указанной стратегией"""
        entities = set()
        
        # Для стратегии перекрытия возвращаем все поверхностные сущности
        if strategy.get_render_priority() == 3:  # OverlayRenderStrategy
            entities.update(self.entities_by_z_level.get(0, set()))
        else:
            # Для обычных стратегий возвращаем сущности соответствующего Z-уровня
            if strategy.get_render_priority() == 0:  # Underground
                entities.update(self.entities_by_z_level.get(-1, set()))
            elif strategy.get_render_priority() == 1:  # Surface
                entities.update(self.entities_by_z_level.get(0, set()))
            elif strategy.get_render_priority() == 2:  # Elevated
                entities.update(self.entities_by_z_level.get(1, set()))
                
        return entities
        
    def _filter_visible_entities(self, entities: Set[Entity], 
                                camera_offset: Tuple[float, float]) -> List[Entity]:
        """Отфильтровать только видимые на экране сущности"""
        visible_entities = []
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Расширяем область видимости для предзагрузки
        margin = 64  # Дополнительные пиксели за границами экрана
        
        for entity in entities:
            pos_comp = entity.get_component(PositionComponent)
            if not pos_comp:
                continue
                
            # Проверяем, находится ли сущность в области видимости
            entity_screen_x = pos_comp.x - camera_offset[0]
            entity_screen_y = pos_comp.y - camera_offset[1]
            
            if (-margin <= entity_screen_x <= screen_width + margin and
                -margin <= entity_screen_y <= screen_height + margin):
                visible_entities.append(entity)
                
        # Сортируем по Y-координате для правильного порядка рендеринга
        visible_entities.sort(key=lambda e: e.get_component(PositionComponent).y)
        
        return visible_entities
        
    def set_player_z_level(self, z_level: int):
        """Установить Z-уровень игрока для эффектов перекрытия"""
        if self.player_z_level != z_level:
            self.player_z_level = z_level
            
            # Обновляем стратегию перекрытия
            self.overlay_strategy = StrategyFactory.create_strategy(
                0, is_overlay=True, player_z_level=z_level
            )
            
    def add_entity_to_render(self, entity: Entity):
        """Добавить сущность для рендеринга"""
        pos_comp = entity.get_component(PositionComponent)
        if pos_comp:
            z_level = pos_comp.z
            if z_level not in self.entities_by_z_level:
                self.entities_by_z_level[z_level] = set()
            self.entities_by_z_level[z_level].add(entity)
            
    def remove_entity_from_render(self, entity: Entity):
        """Удалить сущность из рендеринга"""
        pos_comp = entity.get_component(PositionComponent)
        if pos_comp:
            z_level = pos_comp.z
            if z_level in self.entities_by_z_level:
                self.entities_by_z_level[z_level].discard(entity)
                
    def invalidate_cache(self):
        """Пометить кэш как устаревший"""
        self.cache_dirty = True
        
    def get_render_stats(self) -> Dict[str, int]:
        """Получить статистику рендеринга"""
        stats = {
            'total_entities': sum(len(entities) for entities in self.entities_by_z_level.values()),
            'underground_entities': len(self.entities_by_z_level.get(-1, set())),
            'surface_entities': len(self.entities_by_z_level.get(0, set())),
            'elevated_entities': len(self.entities_by_z_level.get(1, set())),
            'player_z_level': self.player_z_level,
            'cache_dirty': self.cache_dirty
        }
        return stats
        
    def debug_render_z_levels(self, font: pygame.font.Font):
        """Отладочный рендеринг информации о Z-уровнях"""
        stats = self.get_render_stats()
        y_offset = 10
        
        for key, value in stats.items():
            text = f"{key}: {value}"
            text_surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25


class LayeredWorld:
    """Класс для представления многослойного мира"""
    
    def __init__(self, world_id: str, surface_map_data: List, underground_map_data: List = None):
        self.world_id = world_id
        self.surface_map = surface_map_data
        self.underground_map = underground_map_data or []
        self.elevated_map = []  # Для будущего расширения
        
        # Проверяем совпадение размеров карт
        if self.underground_map and len(self.surface_map) != len(self.underground_map):
            raise ValueError("Surface and underground maps must have the same dimensions")
            
    def get_tile_at_layer(self, x: int, y: int, z: int):
        """Получить тайл на указанном слое и позиции"""
        if z == 0 and self.surface_map:
            return self._get_tile_from_map(self.surface_map, x, y)
        elif z == -1 and self.underground_map:
            return self._get_tile_from_map(self.underground_map, x, y)
        elif z == 1 and self.elevated_map:
            return self._get_tile_from_map(self.elevated_map, x, y)
        return None
        
    def _get_tile_from_map(self, map_data: List, x: int, y: int):
        """Получить тайл из карты по координатам"""
        if 0 <= y < len(map_data) and 0 <= x < len(map_data[y]):
            return map_data[y][x]
        return None
        
    def has_layer(self, z: int) -> bool:
        """Проверить, существует ли указанный слой"""
        if z == 0:
            return bool(self.surface_map)
        elif z == -1:
            return bool(self.underground_map)
        elif z == 1:
            return bool(self.elevated_map)
        return False
        
    def get_available_layers(self) -> List[int]:
        """Получить список доступных Z-уровней"""
        layers = []
        if self.underground_map:
            layers.append(-1)
        if self.surface_map:
            layers.append(0)
        if self.elevated_map:
            layers.append(1)
        return sorted(layers)