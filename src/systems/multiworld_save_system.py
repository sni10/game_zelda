"""
Расширенная система сохранений для поддержки множественных миров и Z-координат
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.core.ecs.entity import Entity, EntityManager
from src.core.ecs.component import (
    PositionComponent, ZLevelComponent, WorldComponent, 
    TunnelComponent, PortalComponent, RenderLayerComponent
)
from src.world.world_manager import WorldManager
from src.rendering.layer_renderer import LayeredWorld


class MultiWorldSaveSystem:
    """Система сохранения для множественных миров и ECS архитектуры"""
    
    def __init__(self, entity_manager: EntityManager, world_manager: WorldManager):
        self.entity_manager = entity_manager
        self.world_manager = world_manager
        self.save_version = "2.0"  # Новая версия для поддержки множественных миров
        self.saves_dir = "saves"
        self.quicksave_file = "multiworld_quicksave.json"
        
        # Создаем папку сохранений если её нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
            
        # Регистрируем сериализаторы компонентов
        self.component_serializers = {
            PositionComponent: self._serialize_position_component,
            ZLevelComponent: self._serialize_z_level_component,
            WorldComponent: self._serialize_world_component,
            TunnelComponent: self._serialize_tunnel_component,
            PortalComponent: self._serialize_portal_component,
            RenderLayerComponent: self._serialize_render_layer_component
        }
        
        # Регистрируем десериализаторы компонентов
        self.component_deserializers = {
            'PositionComponent': self._deserialize_position_component,
            'ZLevelComponent': self._deserialize_z_level_component,
            'WorldComponent': self._deserialize_world_component,
            'TunnelComponent': self._deserialize_tunnel_component,
            'PortalComponent': self._deserialize_portal_component,
            'RenderLayerComponent': self._deserialize_render_layer_component
        }
    
    def save_game(self, player_entity: Entity, game_stats: Optional[Dict] = None, 
                  filename: Optional[str] = None) -> bool:
        """
        Сохранение полного состояния игры с множественными мирами
        
        Args:
            player_entity: сущность игрока
            game_stats: статистика игры
            filename: имя файла сохранения
            
        Returns:
            bool: успешность сохранения
        """
        try:
            if filename is None:
                filename = self.quicksave_file
                
            filepath = os.path.join(self.saves_dir, filename)
            
            # Создаем структуру сохранения
            save_data = {
                "version": self.save_version,
                "timestamp": datetime.now().isoformat() + "Z",
                "player": self._serialize_player_entity(player_entity),
                "worlds": self._serialize_all_worlds(),
                "current_world": self.world_manager.current_world_id,
                "world_states": self._serialize_world_states(),
                "game_stats": game_stats or self._get_default_game_stats()
            }
            
            # Записываем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print(f"Multiworld game saved: {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving multiworld game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_game(self, filename: Optional[str] = None) -> Optional[Dict]:
        """
        Загрузка состояния игры с множественными мирами
        
        Args:
            filename: имя файла сохранения
            
        Returns:
            Dict: данные сохранения или None
        """
        try:
            if filename is None:
                filename = self.quicksave_file
                
            filepath = os.path.join(self.saves_dir, filename)
            
            if not os.path.exists(filepath):
                print(f"Save file not found: {filename}")
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                
            # Проверяем версию
            if save_data.get("version") != self.save_version:
                print(f"Warning: save version {save_data.get('version')} differs from current {self.save_version}")
                
            print(f"Multiworld game loaded: {filename}")
            return save_data
            
        except Exception as e:
            print(f"Error loading multiworld game: {e}")
            return None
    
    def apply_save_data(self, save_data: Dict, player_entity: Entity) -> bool:
        """
        Применить загруженные данные к игре
        
        Args:
            save_data: данные сохранения
            player_entity: сущность игрока
            
        Returns:
            bool: успешность применения
        """
        try:
            # Восстанавливаем состояние игрока
            self._apply_player_data(save_data["player"], player_entity)
            
            # Восстанавливаем миры
            self._apply_worlds_data(save_data["worlds"])
            
            # Восстанавливаем состояния миров
            self._apply_world_states_data(save_data["world_states"])
            
            # Переключаемся на сохраненный мир
            current_world = save_data.get("current_world")
            if current_world:
                self.world_manager.switch_to_world(current_world, player_entity)
                
            print("Save data applied successfully")
            return True
            
        except Exception as e:
            print(f"Error applying save data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _serialize_player_entity(self, player_entity: Entity) -> Dict:
        """Сериализация сущности игрока"""
        player_data = {
            "entity_id": player_entity.id,
            "components": {}
        }
        
        # Сериализуем все компоненты игрока
        for comp_type, component in player_entity.components.items():
            serializer = self.component_serializers.get(comp_type)
            if serializer:
                player_data["components"][comp_type.__name__] = serializer(component)
            else:
                # Базовая сериализация для неизвестных компонентов
                if hasattr(component, '__dict__'):
                    player_data["components"][comp_type.__name__] = component.__dict__.copy()
                    
        return player_data
    
    def _serialize_all_worlds(self) -> Dict:
        """Сериализация всех миров"""
        worlds_data = {}
        
        for world_id, world_state in self.world_manager.world_states.items():
            worlds_data[world_id] = {
                "world_type": self._get_world_type(world_state.world),
                "size": (world_state.world.surface_map and len(world_state.world.surface_map[0]) * 32 or 800,
                        world_state.world.surface_map and len(world_state.world.surface_map) * 32 or 600),
                "entities": self._serialize_world_entities(world_state.entities)
            }
            
        return worlds_data
    
    def _serialize_world_states(self) -> Dict:
        """Сериализация состояний миров"""
        states_data = {}
        
        for world_id, world_state in self.world_manager.world_states.items():
            states_data[world_id] = {
                "is_loaded": world_state.is_loaded,
                "is_active": world_state.is_active,
                "last_player_position": world_state.last_player_position,
                "world_data": world_state.world_data
            }
            
        return states_data
    
    def _serialize_world_entities(self, entities: List[Entity]) -> List[Dict]:
        """Сериализация сущностей мира"""
        entities_data = []
        
        for entity in entities:
            entity_data = {
                "entity_id": entity.id,
                "active": entity.active,
                "components": {}
            }
            
            # Сериализуем компоненты
            for comp_type, component in entity.components.items():
                serializer = self.component_serializers.get(comp_type)
                if serializer:
                    entity_data["components"][comp_type.__name__] = serializer(component)
                else:
                    # Базовая сериализация
                    if hasattr(component, '__dict__'):
                        entity_data["components"][comp_type.__name__] = component.__dict__.copy()
                        
            entities_data.append(entity_data)
            
        return entities_data
    
    def _apply_player_data(self, player_data: Dict, player_entity: Entity):
        """Применить данные игрока"""
        # Восстанавливаем компоненты игрока
        for comp_name, comp_data in player_data["components"].items():
            deserializer = self.component_deserializers.get(comp_name)
            if deserializer:
                component = deserializer(comp_data)
                player_entity.add_component(component)
    
    def _apply_worlds_data(self, worlds_data: Dict):
        """Применить данные миров"""
        # Очищаем существующие миры
        self.world_manager.world_states.clear()
        
        # Восстанавливаем миры
        for world_id, world_data in worlds_data.items():
            world_type = world_data["world_type"]
            size = tuple(world_data["size"])
            
            # Создаем мир
            success = self.world_manager.create_world(world_type, world_id, size)
            if success:
                # Восстанавливаем сущности мира
                world_state = self.world_manager.world_states[world_id]
                world_state.entities.clear()
                
                for entity_data in world_data["entities"]:
                    entity = self._deserialize_entity(entity_data)
                    if entity:
                        world_state.entities.append(entity)
                        self.world_manager.entity_world_cache[entity.id] = world_id
    
    def _apply_world_states_data(self, states_data: Dict):
        """Применить состояния миров"""
        for world_id, state_data in states_data.items():
            if world_id in self.world_manager.world_states:
                world_state = self.world_manager.world_states[world_id]
                world_state.is_loaded = state_data["is_loaded"]
                world_state.is_active = state_data["is_active"]
                world_state.last_player_position = tuple(state_data["last_player_position"])
                world_state.world_data = state_data["world_data"]
    
    def _deserialize_entity(self, entity_data: Dict) -> Optional[Entity]:
        """Десериализация сущности"""
        try:
            entity = self.entity_manager.create_entity()
            entity.active = entity_data["active"]
            
            # Восстанавливаем компоненты
            for comp_name, comp_data in entity_data["components"].items():
                deserializer = self.component_deserializers.get(comp_name)
                if deserializer:
                    component = deserializer(comp_data)
                    entity.add_component(component)
                    
            return entity
            
        except Exception as e:
            print(f"Error deserializing entity: {e}")
            return None
    
    def _get_world_type(self, world: LayeredWorld) -> str:
        """Определить тип мира"""
        # Простая логика определения типа по ID
        if "cave" in world.world_id:
            return "cave"
        elif "underground" in world.world_id:
            return "underground"
        else:
            return "main"
    
    def _get_default_game_stats(self) -> Dict:
        """Получить статистику игры по умолчанию"""
        return {
            "play_time": 0,
            "worlds_visited": 0,
            "z_transitions": 0,
            "portal_uses": 0,
            "enemies_killed": 0,
            "items_collected": 0
        }
    
    # Сериализаторы компонентов
    def _serialize_position_component(self, component: PositionComponent) -> Dict:
        return {
            "x": component.x,
            "y": component.y,
            "z": component.z,
            "world_id": component.world_id,
            "previous_z": component.previous_z,
            "previous_world": component.previous_world
        }
    
    def _serialize_z_level_component(self, component: ZLevelComponent) -> Dict:
        return {
            "current_level": component.current_level,
            "can_change_levels": component.can_change_levels,
            "transition_cooldown": component.transition_cooldown,
            "transition_in_progress": component.transition_in_progress
        }
    
    def _serialize_world_component(self, component: WorldComponent) -> Dict:
        return {
            "world_id": component.world_id,
            "world_type": component.world_type,
            "width": component.width,
            "height": component.height,
            "is_active": component.is_active,
            "entities": list(component.entities)
        }
    
    def _serialize_tunnel_component(self, component: TunnelComponent) -> Dict:
        return {
            "entrance_pos": component.entrance_pos,
            "exit_pos": component.exit_pos,
            "length": component.length,
            "width": component.width,
            "tunnel_path": component.tunnel_path,
            "is_active": component.is_active
        }
    
    def _serialize_portal_component(self, component: PortalComponent) -> Dict:
        return {
            "target_world": component.target_world,
            "target_position": component.target_position,
            "target_z": component.target_z,
            "activation_requirements": component.activation_requirements,
            "visual_effects": component.visual_effects,
            "is_active": component.is_active,
            "cooldown": component.cooldown
        }
    
    def _serialize_render_layer_component(self, component: RenderLayerComponent) -> Dict:
        return {
            "layer": component.layer,
            "alpha": component.alpha,
            "visible": component.visible,
            "render_priority": component.render_priority
        }
    
    # Десериализаторы компонентов
    def _deserialize_position_component(self, data: Dict) -> PositionComponent:
        component = PositionComponent(data["x"], data["y"], data["z"], data["world_id"])
        component.previous_z = data["previous_z"]
        component.previous_world = data["previous_world"]
        return component
    
    def _deserialize_z_level_component(self, data: Dict) -> ZLevelComponent:
        component = ZLevelComponent(data["current_level"])
        component.can_change_levels = data["can_change_levels"]
        component.transition_cooldown = data["transition_cooldown"]
        component.transition_in_progress = data["transition_in_progress"]
        return component
    
    def _deserialize_world_component(self, data: Dict) -> WorldComponent:
        component = WorldComponent(data["world_id"], data["world_type"], (data["width"], data["height"]))
        component.is_active = data["is_active"]
        component.entities = set(data["entities"])
        return component
    
    def _deserialize_tunnel_component(self, data: Dict) -> TunnelComponent:
        component = TunnelComponent(
            tuple(data["entrance_pos"]), 
            tuple(data["exit_pos"]), 
            data["length"]
        )
        component.width = data["width"]
        component.tunnel_path = [tuple(pos) for pos in data["tunnel_path"]]
        component.is_active = data["is_active"]
        return component
    
    def _deserialize_portal_component(self, data: Dict) -> PortalComponent:
        component = PortalComponent(
            data["target_world"],
            tuple(data["target_position"]),
            data["target_z"]
        )
        component.activation_requirements = data["activation_requirements"]
        component.visual_effects = data["visual_effects"]
        component.is_active = data["is_active"]
        component.cooldown = data["cooldown"]
        return component
    
    def _deserialize_render_layer_component(self, data: Dict) -> RenderLayerComponent:
        component = RenderLayerComponent(data["layer"], data["alpha"])
        component.visible = data["visible"]
        component.render_priority = data["render_priority"]
        return component
    
    def quicksave_exists(self) -> bool:
        """Проверка существования файла быстрого сохранения"""
        filepath = os.path.join(self.saves_dir, self.quicksave_file)
        return os.path.exists(filepath)
    
    def get_save_info(self, filename: Optional[str] = None) -> Optional[Dict]:
        """Получить информацию о сохранении без полной загрузки"""
        try:
            if filename is None:
                filename = self.quicksave_file
                
            filepath = os.path.join(self.saves_dir, filename)
            
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                
            return {
                "version": save_data.get("version"),
                "timestamp": save_data.get("timestamp"),
                "current_world": save_data.get("current_world"),
                "worlds_count": len(save_data.get("worlds", {})),
                "game_stats": save_data.get("game_stats", {})
            }
            
        except Exception as e:
            print(f"Error getting save info: {e}")
            return None