"""
Strategy Pattern для рендеринга разных Z-уровней
"""
import pygame
from abc import ABC, abstractmethod
from typing import Tuple
from src.core.ecs.entity import Entity
from src.core.ecs.component import PositionComponent, RenderLayerComponent


class LayerRenderStrategy(ABC):
    """Стратегия рендеринга для разных Z-уровней"""
    
    @abstractmethod
    def render(self, entity: Entity, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Отрендерить сущность с учетом стратегии слоя"""
        pass
    
    @abstractmethod
    def get_render_priority(self) -> int:
        """Получить приоритет рендеринга (больше = рендерится позже)"""
        pass


class SurfaceRenderStrategy(LayerRenderStrategy):
    """Рендеринг поверхностного уровня (Z = 0)"""
    
    def render(self, entity: Entity, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Обычный рендеринг для поверхностного уровня"""
        pos_comp = entity.get_component(PositionComponent)
        layer_comp = entity.get_component(RenderLayerComponent)
        
        if not pos_comp or not layer_comp or pos_comp.z != 0:
            return
            
        # Вычисляем позицию на экране
        screen_x = int(pos_comp.x - camera_offset[0])
        screen_y = int(pos_comp.y - camera_offset[1])
        
        # Простой рендеринг как цветной прямоугольник (будет заменен на спрайты)
        color = self._get_entity_color(entity)
        size = 32  # Размер тайла
        
        if layer_comp.visible and layer_comp.alpha > 0:
            if layer_comp.alpha < 255:
                # Создаем поверхность с альфа-каналом
                temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                temp_surface.fill((*color, layer_comp.alpha))
                screen.blit(temp_surface, (screen_x, screen_y))
            else:
                # Обычный рендеринг
                pygame.draw.rect(screen, color, (screen_x, screen_y, size, size))
    
    def get_render_priority(self) -> int:
        return 1  # Средний приоритет
    
    def _get_entity_color(self, entity: Entity) -> Tuple[int, int, int]:
        """Получить цвет сущности (временная реализация)"""
        # Временная логика для определения цвета
        from src.core.ecs.component import TunnelComponent, PortalComponent
        
        if entity.has_component(TunnelComponent):
            return (139, 69, 19)  # Коричневый для тоннелей
        elif entity.has_component(PortalComponent):
            return (128, 0, 128)  # Фиолетовый для порталов
        else:
            return (0, 128, 0)  # Зеленый по умолчанию


class UndergroundRenderStrategy(LayerRenderStrategy):
    """Рендеринг подземного уровня (Z = -1)"""
    
    def render(self, entity: Entity, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Затемненный рендеринг для подземелий"""
        pos_comp = entity.get_component(PositionComponent)
        layer_comp = entity.get_component(RenderLayerComponent)
        
        if not pos_comp or not layer_comp or pos_comp.z != -1:
            return
            
        # Вычисляем позицию на экране
        screen_x = int(pos_comp.x - camera_offset[0])
        screen_y = int(pos_comp.y - camera_offset[1])
        
        # Затемненный рендеринг для подземелий
        color = self._get_darkened_color(entity)
        size = 32
        
        if layer_comp.visible and layer_comp.alpha > 0:
            # Создаем затемненную поверхность
            temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            alpha = min(layer_comp.alpha, 200)  # Максимальная прозрачность для подземелий
            temp_surface.fill((*color, alpha))
            screen.blit(temp_surface, (screen_x, screen_y))
            
            # Добавляем эффект подземелья (темная рамка)
            pygame.draw.rect(screen, (50, 50, 50), (screen_x, screen_y, size, size), 2)
    
    def get_render_priority(self) -> int:
        return 0  # Низкий приоритет - рендерится первым
    
    def _get_darkened_color(self, entity: Entity) -> Tuple[int, int, int]:
        """Получить затемненный цвет для подземелий"""
        from src.core.ecs.component import TunnelComponent
        
        if entity.has_component(TunnelComponent):
            return (101, 67, 33)  # Темно-коричневый для тоннелей
        else:
            return (64, 64, 64)  # Темно-серый по умолчанию


class ElevatedRenderStrategy(LayerRenderStrategy):
    """Рендеринг надземного уровня (Z = +1)"""
    
    def render(self, entity: Entity, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Рендеринг для мостов, крыш, верхушек деревьев"""
        pos_comp = entity.get_component(PositionComponent)
        layer_comp = entity.get_component(RenderLayerComponent)
        
        if not pos_comp or not layer_comp or pos_comp.z != 1:
            return
            
        # Вычисляем позицию на экране
        screen_x = int(pos_comp.x - camera_offset[0])
        screen_y = int(pos_comp.y - camera_offset[1])
        
        # Яркий рендеринг для надземных объектов
        color = self._get_elevated_color(entity)
        size = 32
        
        if layer_comp.visible and layer_comp.alpha > 0:
            if layer_comp.alpha < 255:
                temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                temp_surface.fill((*color, layer_comp.alpha))
                screen.blit(temp_surface, (screen_x, screen_y))
            else:
                pygame.draw.rect(screen, color, (screen_x, screen_y, size, size))
                
            # Добавляем эффект высоты (светлая рамка)
            pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, size, size), 1)
    
    def get_render_priority(self) -> int:
        return 2  # Высокий приоритет - рендерится последним
    
    def _get_elevated_color(self, entity: Entity) -> Tuple[int, int, int]:
        """Получить цвет для надземных объектов"""
        return (160, 160, 160)  # Светло-серый для мостов/крыш


class OverlayRenderStrategy(LayerRenderStrategy):
    """Рендеринг перекрывающих объектов (трава над тоннелями)"""
    
    def __init__(self, player_z_level: int = 0):
        self.player_z_level = player_z_level
    
    def render(self, entity: Entity, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Полупрозрачный рендеринг для перекрытий"""
        pos_comp = entity.get_component(PositionComponent)
        layer_comp = entity.get_component(RenderLayerComponent)
        
        if not pos_comp or not layer_comp:
            return
            
        # Проверяем, нужно ли применять эффект перекрытия
        should_overlay = self._should_apply_overlay(entity)
        
        if not should_overlay:
            return
            
        # Вычисляем позицию на экране
        screen_x = int(pos_comp.x - camera_offset[0])
        screen_y = int(pos_comp.y - camera_offset[1])
        
        # Полупрозрачный рендеринг
        color = self._get_overlay_color(entity)
        size = 32
        overlay_alpha = 128  # 50% прозрачность для эффекта перекрытия
        
        temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        temp_surface.fill((*color, overlay_alpha))
        screen.blit(temp_surface, (screen_x, screen_y))
    
    def get_render_priority(self) -> int:
        return 3  # Очень высокий приоритет - рендерится поверх всего
    
    def set_player_z_level(self, z_level: int):
        """Установить Z-уровень игрока для определения перекрытий"""
        self.player_z_level = z_level
    
    def _should_apply_overlay(self, entity: Entity) -> bool:
        """Определить, нужно ли применять эффект перекрытия"""
        pos_comp = entity.get_component(PositionComponent)
        
        # Применяем перекрытие, если игрок находится под объектом
        return (pos_comp.z > self.player_z_level and 
                self.player_z_level == -1)  # Игрок в тоннеле
    
    def _get_overlay_color(self, entity: Entity) -> Tuple[int, int, int]:
        """Получить цвет для перекрывающего объекта"""
        return (0, 150, 0)  # Зеленый для травы


class StrategyFactory:
    """Фабрика для создания стратегий рендеринга"""
    
    @staticmethod
    def create_strategy(z_level: int, is_overlay: bool = False, 
                       player_z_level: int = 0) -> LayerRenderStrategy:
        """Создать стратегию рендеринга для указанного Z-уровня"""
        if is_overlay:
            return OverlayRenderStrategy(player_z_level)
        elif z_level == -1:
            return UndergroundRenderStrategy()
        elif z_level == 0:
            return SurfaceRenderStrategy()
        elif z_level == 1:
            return ElevatedRenderStrategy()
        else:
            # По умолчанию используем поверхностную стратегию
            return SurfaceRenderStrategy()
    
    @staticmethod
    def get_all_strategies(player_z_level: int = 0) -> list[LayerRenderStrategy]:
        """Получить все стратегии рендеринга в порядке приоритета"""
        strategies = [
            UndergroundRenderStrategy(),
            SurfaceRenderStrategy(),
            ElevatedRenderStrategy(),
            OverlayRenderStrategy(player_z_level)
        ]
        
        # Сортируем по приоритету рендеринга
        return sorted(strategies, key=lambda s: s.get_render_priority())