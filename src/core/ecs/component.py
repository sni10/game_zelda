"""
Базовые классы для ECS (Entity Component System) архитектуры
"""
from abc import ABC
from typing import Dict, Any


class Component(ABC):
    """Базовый класс для всех компонентов в ECS"""
    pass


class PositionComponent(Component):
    """Расширенный компонент позиции с Z-координатой и world_id"""
    def __init__(self, x: float, y: float, z: int = 0, world_id: str = "main"):
        self.x = x
        self.y = y
        self.z = z  # -1: подземный, 0: базовый, +1: надземный
        self.world_id = world_id  # идентификатор мира
        self.previous_z = z
        self.previous_world = world_id
        
    def set_position(self, x: float, y: float, z: int = None, world_id: str = None):
        """Установить новую позицию с сохранением предыдущей"""
        self.previous_z = self.z
        self.previous_world = self.world_id
        
        self.x = x
        self.y = y
        if z is not None:
            self.z = z
        if world_id is not None:
            self.world_id = world_id


class ZLevelComponent(Component):
    """Компонент для управления Z-уровнями"""
    def __init__(self, current_level: int = 0):
        self.current_level = current_level
        self.can_change_levels = True
        self.transition_cooldown = 0
        self.transition_in_progress = False
        
    def start_transition(self, target_level: int, cooldown_ms: int = 1000):
        """Начать переход на новый Z-уровень"""
        if self.can_change_levels and not self.transition_in_progress:
            self.transition_in_progress = True
            self.transition_cooldown = cooldown_ms
            return True
        return False
        
    def complete_transition(self, new_level: int):
        """Завершить переход на новый Z-уровень"""
        self.current_level = new_level
        self.transition_in_progress = False


class WorldComponent(Component):
    """Базовый компонент мира"""
    def __init__(self, world_id: str, world_type: str, size: tuple):
        self.world_id = world_id
        self.world_type = world_type  # "main", "cave", "underground", "ice", "forest"
        self.width, self.height = size
        self.is_active = False
        self.entities = set()
        
    def add_entity(self, entity_id: int):
        """Добавить сущность в мир"""
        self.entities.add(entity_id)
        
    def remove_entity(self, entity_id: int):
        """Удалить сущность из мира"""
        self.entities.discard(entity_id)


class TunnelComponent(Component):
    """Компонент тоннеля"""
    def __init__(self, entrance_pos: tuple, exit_pos: tuple, length: int):
        self.entrance_pos = entrance_pos  # (x, y) координаты входа
        self.exit_pos = exit_pos  # (x, y) координаты выхода
        self.length = length  # длина тоннеля в клетках
        self.width = 2  # ширина тоннеля в клетках
        self.tunnel_path = self._generate_path()
        self.is_active = True
        
    def _generate_path(self):
        """Генерация пути тоннеля между входом и выходом"""
        path = []
        start_x, start_y = self.entrance_pos
        end_x, end_y = self.exit_pos
        
        # Простая линейная интерполяция для создания пути
        for i in range(self.length + 1):
            t = i / self.length if self.length > 0 else 0
            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t)
            path.append((x, y))
            
        return path


class PortalComponent(Component):
    """Компонент портала для телепортации между мирами"""
    def __init__(self, target_world: str, target_position: tuple, target_z: int = 0):
        self.target_world = target_world
        self.target_position = target_position  # (x, y)
        self.target_z = target_z  # Z-уровень в целевом мире
        self.activation_requirements = []  # требования для активации
        self.visual_effects = []  # визуальные эффекты
        self.is_active = True
        self.cooldown = 0
        
    def can_activate(self) -> bool:
        """Проверить, можно ли активировать портал"""
        return self.is_active and self.cooldown <= 0
        
    def activate(self, cooldown_ms: int = 2000):
        """Активировать портал с кулдауном"""
        if self.can_activate():
            self.cooldown = cooldown_ms
            return True
        return False


class RenderLayerComponent(Component):
    """Компонент для рендеринга по слоям"""
    def __init__(self, layer: int, alpha: int = 255):
        self.layer = layer  # Z-уровень для рендеринга
        self.alpha = alpha  # прозрачность для эффектов перекрытия
        self.visible = True
        self.render_priority = 0  # приоритет рендеринга внутри слоя
        
    def set_overlay_effect(self, alpha: int):
        """Установить эффект перекрытия"""
        self.alpha = max(0, min(255, alpha))


class LoadingScreenComponent(Component):
    """Компонент экрана загрузки для мира"""
    def __init__(self, background_image: str, story_text: str):
        self.background_image = background_image
        self.story_text = story_text
        self.music_track = None
        self.loading_progress = 0.0
        self.is_complete = False
        
    def update_progress(self, progress: float):
        """Обновить прогресс загрузки"""
        self.loading_progress = max(0.0, min(1.0, progress))
        if self.loading_progress >= 1.0:
            self.is_complete = True