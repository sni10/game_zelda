"""
System классы для ECS архитектуры
"""
from abc import ABC, abstractmethod
from typing import Set, Type, List
from .entity import Entity, EntityManager
from .component import Component


class System(ABC):
    """Базовый класс для всех систем в ECS"""
    
    def __init__(self, entity_manager: EntityManager):
        self.entity_manager = entity_manager
        self.active = True
        self.priority = 0  # Приоритет выполнения системы
        
    @abstractmethod
    def get_required_components(self) -> List[Type[Component]]:
        """Получить список требуемых компонентов для системы"""
        pass
        
    @abstractmethod
    def update(self, dt: float):
        """Обновить систему"""
        pass
        
    def get_entities(self) -> Set[Entity]:
        """Получить все сущности с требуемыми компонентами"""
        required_components = self.get_required_components()
        if not required_components:
            return set()
        return self.entity_manager.get_entities_with_components(*required_components)
        
    def set_active(self, active: bool):
        """Установить активность системы"""
        self.active = active
        
    def is_active(self) -> bool:
        """Проверить активность системы"""
        return self.active


class SystemManager:
    """Менеджер для управления системами"""
    
    def __init__(self, entity_manager: EntityManager):
        self.entity_manager = entity_manager
        self.systems: List[System] = []
        
    def add_system(self, system: System):
        """Добавить систему"""
        self.systems.append(system)
        # Сортируем по приоритету (больший приоритет = раньше выполняется)
        self.systems.sort(key=lambda s: s.priority, reverse=True)
        
    def remove_system(self, system_type: Type[System]) -> bool:
        """Удалить систему по типу"""
        for i, system in enumerate(self.systems):
            if isinstance(system, system_type):
                del self.systems[i]
                return True
        return False
        
    def get_system(self, system_type: Type[System]) -> System:
        """Получить систему по типу"""
        for system in self.systems:
            if isinstance(system, system_type):
                return system
        return None
        
    def update_all(self, dt: float):
        """Обновить все активные системы"""
        for system in self.systems:
            if system.is_active():
                system.update(dt)
                
    def set_system_active(self, system_type: Type[System], active: bool):
        """Установить активность системы"""
        system = self.get_system(system_type)
        if system:
            system.set_active(active)
            
    def clear_all(self):
        """Очистить все системы"""
        self.systems.clear()


class MovementSystem(System):
    """Система движения сущностей"""
    
    def get_required_components(self) -> List[Type[Component]]:
        from .component import PositionComponent
        return [PositionComponent]
        
    def update(self, dt: float):
        """Обновление движения"""
        # Базовая реализация - будет расширена в конкретных системах
        pass


class RenderSystem(System):
    """Базовая система рендеринга"""
    
    def __init__(self, entity_manager: EntityManager, screen):
        super().__init__(entity_manager)
        self.screen = screen
        self.camera_x = 0
        self.camera_y = 0
        
    def get_required_components(self) -> List[Type[Component]]:
        from .component import PositionComponent, RenderLayerComponent
        return [PositionComponent, RenderLayerComponent]
        
    def update(self, dt: float):
        """Базовое обновление рендеринга"""
        pass
        
    def set_camera(self, x: float, y: float):
        """Установить позицию камеры"""
        self.camera_x = x
        self.camera_y = y


class CollisionSystem(System):
    """Система коллизий"""
    
    def get_required_components(self) -> List[Type[Component]]:
        from .component import PositionComponent
        return [PositionComponent]
        
    def update(self, dt: float):
        """Обновление коллизий"""
        # Базовая реализация - будет расширена
        pass
        
    def check_collision(self, entity1: Entity, entity2: Entity) -> bool:
        """Проверить коллизию между двумя сущностями"""
        # Базовая реализация
        return False


class ZTransitionSystem(System):
    """Система переходов между Z-уровнями"""
    
    def __init__(self, entity_manager: EntityManager):
        super().__init__(entity_manager)
        self.priority = 10  # Высокий приоритет для переходов
        
    def get_required_components(self) -> List[Type[Component]]:
        from .component import PositionComponent, ZLevelComponent
        return [PositionComponent, ZLevelComponent]
        
    def update(self, dt: float):
        """Обновление переходов между Z-уровнями"""
        entities = self.get_entities()
        
        for entity in entities:
            from .component import ZLevelComponent
            z_comp = entity.get_component(ZLevelComponent)
            
            if z_comp.transition_in_progress:
                # Обновляем кулдаун перехода
                z_comp.transition_cooldown -= dt * 1000  # dt в секундах, cooldown в мс
                
                if z_comp.transition_cooldown <= 0:
                    # Переход завершен
                    z_comp.transition_in_progress = False
                    z_comp.can_change_levels = True
                    
    def initiate_z_transition(self, entity: Entity, target_z: int) -> bool:
        """Инициировать переход на новый Z-уровень"""
        from .component import PositionComponent, ZLevelComponent
        
        if not entity.has_components(PositionComponent, ZLevelComponent):
            return False
            
        pos_comp = entity.get_component(PositionComponent)
        z_comp = entity.get_component(ZLevelComponent)
        
        if z_comp.start_transition(target_z):
            pos_comp.set_position(pos_comp.x, pos_comp.y, target_z)
            z_comp.complete_transition(target_z)
            return True
            
        return False


class PortalSystem(System):
    """Система порталов для переходов между мирами"""
    
    def __init__(self, entity_manager: EntityManager):
        super().__init__(entity_manager)
        self.priority = 9  # Высокий приоритет для порталов
        
    def get_required_components(self) -> List[Type[Component]]:
        from .component import PositionComponent, PortalComponent
        return [PositionComponent, PortalComponent]
        
    def update(self, dt: float):
        """Обновление порталов"""
        entities = self.get_entities()
        
        for entity in entities:
            from .component import PortalComponent
            portal_comp = entity.get_component(PortalComponent)
            
            if portal_comp.cooldown > 0:
                portal_comp.cooldown -= dt * 1000  # dt в секундах, cooldown в мс
                
    def activate_portal(self, portal_entity: Entity, traveler_entity: Entity) -> bool:
        """Активировать портал для путешественника"""
        from .component import PositionComponent, PortalComponent
        
        if not portal_entity.has_component(PortalComponent):
            return False
            
        if not traveler_entity.has_component(PositionComponent):
            return False
            
        portal_comp = portal_entity.get_component(PortalComponent)
        traveler_pos = traveler_entity.get_component(PositionComponent)
        
        if portal_comp.activate():
            # Телепортируем путешественника
            target_x, target_y = portal_comp.target_position
            traveler_pos.set_position(
                target_x, 
                target_y, 
                portal_comp.target_z, 
                portal_comp.target_world
            )
            return True
            
        return False
        
    def check_portal_proximity(self, portal_entity: Entity, traveler_entity: Entity, 
                             activation_distance: float = 32.0) -> bool:
        """Проверить близость к порталу для активации"""
        from .component import PositionComponent
        
        if not portal_entity.has_component(PositionComponent):
            return False
            
        if not traveler_entity.has_component(PositionComponent):
            return False
            
        portal_pos = portal_entity.get_component(PositionComponent)
        traveler_pos = traveler_entity.get_component(PositionComponent)
        
        # Проверяем только если в том же мире и на том же Z-уровне
        if (portal_pos.world_id != traveler_pos.world_id or 
            portal_pos.z != traveler_pos.z):
            return False
            
        # Вычисляем расстояние
        dx = portal_pos.x - traveler_pos.x
        dy = portal_pos.y - traveler_pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        return distance <= activation_distance