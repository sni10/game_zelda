"""
Entity класс для ECS архитектуры
"""
from typing import Dict, Type, Optional, Set
from .component import Component


class Entity:
    """Базовый класс сущности в ECS"""
    
    _next_id = 1
    
    def __init__(self):
        self.id = Entity._next_id
        Entity._next_id += 1
        self.components: Dict[Type[Component], Component] = {}
        self.active = True
        
    def add_component(self, component: Component) -> 'Entity':
        """Добавить компонент к сущности"""
        self.components[type(component)] = component
        return self
        
    def remove_component(self, component_type: Type[Component]) -> bool:
        """Удалить компонент из сущности"""
        if component_type in self.components:
            del self.components[component_type]
            return True
        return False
        
    def get_component(self, component_type: Type[Component]) -> Optional[Component]:
        """Получить компонент сущности"""
        return self.components.get(component_type)
        
    def has_component(self, component_type: Type[Component]) -> bool:
        """Проверить наличие компонента"""
        return component_type in self.components
        
    def has_components(self, *component_types: Type[Component]) -> bool:
        """Проверить наличие всех указанных компонентов"""
        return all(comp_type in self.components for comp_type in component_types)
        
    def get_components(self) -> Dict[Type[Component], Component]:
        """Получить все компоненты сущности"""
        return self.components.copy()
        
    def destroy(self):
        """Уничтожить сущность"""
        self.active = False
        self.components.clear()
        
    def __repr__(self):
        return f"Entity(id={self.id}, components={list(self.components.keys())})"


class EntityManager:
    """Менеджер для управления сущностями"""
    
    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self.entities_by_component: Dict[Type[Component], Set[int]] = {}
        
    def create_entity(self) -> Entity:
        """Создать новую сущность"""
        entity = Entity()
        self.entities[entity.id] = entity
        return entity
        
    def destroy_entity(self, entity_id: int) -> bool:
        """Уничтожить сущность"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            
            # Удаляем из индексов компонентов
            for component_type in entity.components.keys():
                if component_type in self.entities_by_component:
                    self.entities_by_component[component_type].discard(entity_id)
                    
            entity.destroy()
            del self.entities[entity_id]
            return True
        return False
        
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Получить сущность по ID"""
        return self.entities.get(entity_id)
        
    def add_component_to_entity(self, entity_id: int, component: Component) -> bool:
        """Добавить компонент к сущности"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.add_component(component)
            
            # Обновляем индекс
            component_type = type(component)
            if component_type not in self.entities_by_component:
                self.entities_by_component[component_type] = set()
            self.entities_by_component[component_type].add(entity_id)
            return True
        return False
        
    def remove_component_from_entity(self, entity_id: int, component_type: Type[Component]) -> bool:
        """Удалить компонент из сущности"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            if entity.remove_component(component_type):
                # Обновляем индекс
                if component_type in self.entities_by_component:
                    self.entities_by_component[component_type].discard(entity_id)
                return True
        return False
        
    def get_entities_with_component(self, component_type: Type[Component]) -> Set[Entity]:
        """Получить все сущности с указанным компонентом"""
        if component_type not in self.entities_by_component:
            return set()
            
        entities = set()
        for entity_id in self.entities_by_component[component_type]:
            if entity_id in self.entities and self.entities[entity_id].active:
                entities.add(self.entities[entity_id])
        return entities
        
    def get_entities_with_components(self, *component_types: Type[Component]) -> Set[Entity]:
        """Получить все сущности с указанными компонентами"""
        if not component_types:
            return set()
            
        # Начинаем с сущностей первого компонента
        result_entities = self.get_entities_with_component(component_types[0])
        
        # Фильтруем по остальным компонентам
        for component_type in component_types[1:]:
            entities_with_comp = self.get_entities_with_component(component_type)
            result_entities = result_entities.intersection(entities_with_comp)
            
        return result_entities
        
    def get_all_entities(self) -> Set[Entity]:
        """Получить все активные сущности"""
        return {entity for entity in self.entities.values() if entity.active}
        
    def cleanup_inactive_entities(self):
        """Очистить неактивные сущности"""
        inactive_ids = [entity_id for entity_id, entity in self.entities.items() if not entity.active]
        for entity_id in inactive_ids:
            self.destroy_entity(entity_id)
            
    def get_entity_count(self) -> int:
        """Получить количество активных сущностей"""
        return len([entity for entity in self.entities.values() if entity.active])
        
    def clear_all(self):
        """Очистить все сущности"""
        for entity in self.entities.values():
            entity.destroy()
        self.entities.clear()
        self.entities_by_component.clear()