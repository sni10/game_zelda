"""
WorldManager - система управления множественными мирами
"""
from typing import Dict, List, Optional, Tuple, Set
from src.core.ecs.entity import Entity, EntityManager
from src.core.ecs.component import PositionComponent, WorldComponent
from src.core.ecs.system import SystemManager, ZTransitionSystem, PortalSystem
from src.rendering.layer_renderer import LayeredWorld, LayerRenderer
from src.factories.world_factory import WorldFactoryRegistry


class WorldState:
    """Состояние мира"""
    
    def __init__(self, world: LayeredWorld, entities: List[Entity]):
        self.world = world
        self.entities = entities
        self.is_loaded = True
        self.is_active = False
        self.last_player_position = (0, 0, 0)  # x, y, z
        self.world_data = {}  # Дополнительные данные мира
        
    def set_player_position(self, x: float, y: float, z: int):
        """Сохранить последнюю позицию игрока в мире"""
        self.last_player_position = (x, y, z)
        
    def get_player_position(self) -> Tuple[float, float, int]:
        """Получить последнюю позицию игрока в мире"""
        return self.last_player_position
        
    def activate(self):
        """Активировать мир"""
        self.is_active = True
        
    def deactivate(self):
        """Деактивировать мир"""
        self.is_active = False
        
    def unload(self):
        """Выгрузить мир из памяти"""
        self.is_loaded = False
        # Можно добавить сериализацию состояния мира


class WorldManager:
    """Менеджер для управления множественными мирами"""
    
    def __init__(self, entity_manager: EntityManager, system_manager: SystemManager,
                 layer_renderer: LayerRenderer):
        self.entity_manager = entity_manager
        self.system_manager = system_manager
        self.layer_renderer = layer_renderer
        
        # Реестр фабрик миров
        self.world_factory_registry = WorldFactoryRegistry(entity_manager)
        
        # Состояния всех миров
        self.world_states: Dict[str, WorldState] = {}
        
        # Текущий активный мир
        self.current_world_id: Optional[str] = None
        
        # Максимальное количество загруженных миров
        self.max_loaded_worlds = 3
        
        # Системы для работы с мирами
        self.z_transition_system = system_manager.get_system(ZTransitionSystem)
        self.portal_system = system_manager.get_system(PortalSystem)
        
        # Кэш для быстрого доступа
        self.entity_world_cache: Dict[int, str] = {}  # entity_id -> world_id
        
    def create_world(self, world_type: str, world_id: str, 
                    size: Tuple[int, int] = (800, 600)) -> bool:
        """Создать новый мир"""
        if world_id in self.world_states:
            print(f"World {world_id} already exists")
            return False
            
        # Создаем мир через фабрику
        world_data = self.world_factory_registry.create_world(world_type, world_id, size)
        if not world_data:
            print(f"Failed to create world {world_id} of type {world_type}")
            return False
            
        world, entities = world_data
        
        # Создаем состояние мира
        world_state = WorldState(world, entities)
        self.world_states[world_id] = world_state
        
        # Обновляем кэш сущностей
        for entity in entities:
            self.entity_world_cache[entity.id] = world_id
            
        print(f"Created world {world_id} of type {world_type} with {len(entities)} entities")
        return True
        
    def load_world(self, world_id: str) -> bool:
        """Загрузить мир в память"""
        if world_id not in self.world_states:
            print(f"World {world_id} does not exist")
            return False
            
        world_state = self.world_states[world_id]
        if world_state.is_loaded:
            return True
            
        # Проверяем лимит загруженных миров
        loaded_count = sum(1 for state in self.world_states.values() if state.is_loaded)
        if loaded_count >= self.max_loaded_worlds:
            self._unload_least_used_world()
            
        # Загружаем мир (в будущем здесь будет загрузка с диска)
        world_state.is_loaded = True
        
        # Добавляем сущности в EntityManager
        for entity in world_state.entities:
            # Сущности уже созданы через EntityManager, просто активируем их
            entity.active = True
            
        print(f"Loaded world {world_id}")
        return True
        
    def unload_world(self, world_id: str) -> bool:
        """Выгрузить мир из памяти"""
        if world_id not in self.world_states:
            return False
            
        if world_id == self.current_world_id:
            print(f"Cannot unload active world {world_id}")
            return False
            
        world_state = self.world_states[world_id]
        if not world_state.is_loaded:
            return True
            
        # Деактивируем сущности
        for entity in world_state.entities:
            entity.active = False
            
        world_state.unload()
        print(f"Unloaded world {world_id}")
        return True
        
    def switch_to_world(self, world_id: str, player_entity: Entity,
                       spawn_position: Optional[Tuple[float, float, int]] = None) -> bool:
        """Переключиться на другой мир"""
        if world_id not in self.world_states:
            print(f"World {world_id} does not exist")
            return False
            
        # Загружаем целевой мир если необходимо
        if not self.load_world(world_id):
            return False
            
        # Сохраняем позицию игрока в текущем мире
        if self.current_world_id:
            current_state = self.world_states[self.current_world_id]
            player_pos = player_entity.get_component(PositionComponent)
            if player_pos:
                current_state.set_player_position(player_pos.x, player_pos.y, player_pos.z)
            current_state.deactivate()
            
        # Активируем новый мир
        new_world_state = self.world_states[world_id]
        new_world_state.activate()
        self.current_world_id = world_id
        
        # Перемещаем игрока
        player_pos = player_entity.get_component(PositionComponent)
        if player_pos:
            if spawn_position:
                x, y, z = spawn_position
            else:
                x, y, z = new_world_state.get_player_position()
                
            player_pos.set_position(x, y, z, world_id)
            
        # Обновляем кэш сущностей
        self.entity_world_cache[player_entity.id] = world_id
        
        # Уведомляем рендерер об изменении мира
        self.layer_renderer.invalidate_cache()
        
        print(f"Switched to world {world_id}")
        return True
        
    def get_current_world(self) -> Optional[LayeredWorld]:
        """Получить текущий активный мир"""
        if not self.current_world_id:
            return None
        return self.world_states[self.current_world_id].world
        
    def get_world(self, world_id: str) -> Optional[LayeredWorld]:
        """Получить мир по ID"""
        if world_id in self.world_states:
            return self.world_states[world_id].world
        return None
        
    def get_world_entities(self, world_id: str) -> List[Entity]:
        """Получить все сущности мира"""
        if world_id in self.world_states:
            return self.world_states[world_id].entities
        return []
        
    def get_current_world_entities(self) -> List[Entity]:
        """Получить сущности текущего мира"""
        if not self.current_world_id:
            return []
        return self.get_world_entities(self.current_world_id)
        
    def add_entity_to_world(self, entity: Entity, world_id: str):
        """Добавить сущность в мир"""
        if world_id not in self.world_states:
            return False
            
        world_state = self.world_states[world_id]
        world_state.entities.append(entity)
        self.entity_world_cache[entity.id] = world_id
        
        # Обновляем позицию сущности
        pos_comp = entity.get_component(PositionComponent)
        if pos_comp:
            pos_comp.world_id = world_id
            
        return True
        
    def remove_entity_from_world(self, entity: Entity, world_id: str):
        """Удалить сущность из мира"""
        if world_id not in self.world_states:
            return False
            
        world_state = self.world_states[world_id]
        if entity in world_state.entities:
            world_state.entities.remove(entity)
            
        if entity.id in self.entity_world_cache:
            del self.entity_world_cache[entity.id]
            
        return True
        
    def get_entity_world(self, entity: Entity) -> Optional[str]:
        """Получить мир, в котором находится сущность"""
        return self.entity_world_cache.get(entity.id)
        
    def handle_portal_activation(self, portal_entity: Entity, traveler_entity: Entity) -> bool:
        """Обработать активацию портала"""
        if not self.portal_system:
            return False
            
        # Проверяем близость к порталу
        if not self.portal_system.check_portal_proximity(portal_entity, traveler_entity):
            return False
            
        # Получаем информацию о портале
        from src.core.ecs.component import PortalComponent
        portal_comp = portal_entity.get_component(PortalComponent)
        if not portal_comp:
            return False
            
        # Переключаемся на целевой мир
        target_position = (*portal_comp.target_position, portal_comp.target_z)
        success = self.switch_to_world(
            portal_comp.target_world, 
            traveler_entity, 
            target_position
        )
        
        if success:
            # Активируем портал (устанавливаем кулдаун)
            portal_comp.activate()
            
        return success
        
    def handle_z_transition(self, entity: Entity, target_z: int) -> bool:
        """Обработать переход между Z-уровнями"""
        if not self.z_transition_system:
            return False
            
        return self.z_transition_system.initiate_z_transition(entity, target_z)
        
    def update(self, dt: float):
        """Обновить менеджер миров"""
        # Обновляем только активный мир
        if self.current_world_id:
            current_state = self.world_states[self.current_world_id]
            
            # Обновляем сущности текущего мира
            for entity in current_state.entities:
                if entity.active:
                    # Здесь можно добавить специфичную для мира логику
                    pass
                    
    def get_world_stats(self) -> Dict[str, any]:
        """Получить статистику миров"""
        stats = {
            'total_worlds': len(self.world_states),
            'loaded_worlds': sum(1 for state in self.world_states.values() if state.is_loaded),
            'active_world': self.current_world_id,
            'available_world_types': self.world_factory_registry.get_available_world_types(),
            'worlds': {}
        }
        
        for world_id, state in self.world_states.items():
            stats['worlds'][world_id] = {
                'loaded': state.is_loaded,
                'active': state.is_active,
                'entity_count': len(state.entities),
                'last_player_position': state.last_player_position
            }
            
        return stats
        
    def _unload_least_used_world(self):
        """Выгрузить наименее используемый мир"""
        # Простая стратегия - выгружаем первый неактивный мир
        for world_id, state in self.world_states.items():
            if state.is_loaded and not state.is_active and world_id != self.current_world_id:
                self.unload_world(world_id)
                break
                
    def cleanup_inactive_entities(self):
        """Очистить неактивные сущности во всех мирах"""
        for world_state in self.world_states.values():
            world_state.entities = [entity for entity in world_state.entities if entity.active]
            
    def save_world_state(self, world_id: str) -> Dict:
        """Сохранить состояние мира (для системы сохранений)"""
        if world_id not in self.world_states:
            return {}
            
        world_state = self.world_states[world_id]
        
        # Сериализуем состояние мира
        state_data = {
            'world_id': world_id,
            'is_loaded': world_state.is_loaded,
            'is_active': world_state.is_active,
            'last_player_position': world_state.last_player_position,
            'world_data': world_state.world_data,
            'entities': []
        }
        
        # Сохраняем состояние сущностей
        for entity in world_state.entities:
            entity_data = {
                'id': entity.id,
                'active': entity.active,
                'components': {}
            }
            
            # Сохраняем компоненты (упрощенная версия)
            for comp_type, component in entity.components.items():
                if hasattr(component, '__dict__'):
                    entity_data['components'][comp_type.__name__] = component.__dict__
                    
            state_data['entities'].append(entity_data)
            
        return state_data
        
    def load_world_state(self, state_data: Dict) -> bool:
        """Загрузить состояние мира (для системы сохранений)"""
        # Упрощенная реализация - в будущем будет более сложная
        world_id = state_data.get('world_id')
        if not world_id:
            return False
            
        # Здесь будет логика восстановления состояния мира
        # Пока просто создаем мир заново
        
        return True