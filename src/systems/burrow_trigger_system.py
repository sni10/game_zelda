"""
Система триггеров для входов и выходов из нор
"""
import math
from src.core.ecs.system import System
from src.core.ecs.component import PositionComponent
from src.components.burrow_components import (
    BurrowEntranceComponent, 
    BurrowExitComponent, 
    UndergroundMovementComponent,
    BurrowAnimationComponent
)


class BurrowTriggerSystem(System):
    """Система триггеров для входов в норы"""
    
    def __init__(self, entity_manager):
        super().__init__(entity_manager)
        self.player_entity = None
    
    def get_required_components(self):
        return [PositionComponent]
    
    def update(self, dt: float):
        """Обновление системы триггеров"""
        player = self._get_player_entity()
        if not player:
            return
            
        player_pos = player.get_component(PositionComponent)
        
        # Проверяем триггеры входов
        self._check_entrance_triggers(player, player_pos)
        
        # Проверяем триггеры выходов (если игрок под землей)
        underground_comp = player.get_component(UndergroundMovementComponent)
        if underground_comp and underground_comp.is_underground:
            self._check_exit_triggers(player, player_pos)
    
    def _get_player_entity(self):
        """Получить сущность игрока"""
        # Простая реализация - ищем первую сущность с определенными компонентами
        # В реальной игре это должно быть более надежно
        for entity in self.entity_manager.entities.values():
            if (entity.has_component(PositionComponent) and 
                hasattr(entity, 'is_player') and entity.is_player):
                return entity
        return None
    
    def _check_entrance_triggers(self, player, player_pos):
        """Проверить триггеры входов в норы"""
        for entity in self.entity_manager.get_entities_with_component(BurrowEntranceComponent):
            entrance_comp = entity.get_component(BurrowEntranceComponent)
            entrance_pos = entity.get_component(PositionComponent)
            
            if not entrance_comp.is_active:
                continue
                
            if self._is_near(player_pos, entrance_pos, 16):
                if entrance_comp.requires_interaction:
                    # Показываем подсказку для взаимодействия
                    self._show_interaction_hint(player)
                else:
                    # Автоматический вход
                    self._trigger_burrow_entrance(player, entity)
    
    def _check_exit_triggers(self, player, player_pos):
        """Проверить триггеры выходов из нор"""
        for entity in self.entity_manager.get_entities_with_component(BurrowExitComponent):
            exit_comp = entity.get_component(BurrowExitComponent)
            exit_pos = entity.get_component(PositionComponent)
            
            if not exit_comp.is_active:
                continue
                
            if self._is_near(player_pos, exit_pos, 16):
                self._trigger_burrow_exit(player, entity)
    
    def _is_near(self, pos1, pos2, distance):
        """Проверить близость двух позиций"""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return math.sqrt(dx * dx + dy * dy) <= distance
    
    def _show_interaction_hint(self, player):
        """Показать подсказку для взаимодействия"""
        # TODO: Реализовать показ подсказки в UI
        pass
    
    def _trigger_burrow_entrance(self, player, entrance_entity):
        """Активация входа в нору"""
        entrance_comp = entrance_entity.get_component(BurrowEntranceComponent)
        
        # Проверяем, не находится ли игрок уже в процессе анимации
        animation_comp = player.get_component(BurrowAnimationComponent)
        if animation_comp and animation_comp.is_active:
            return
        
        # Добавляем компонент подземного движения игроку если его нет
        underground_comp = player.get_component(UndergroundMovementComponent)
        if not underground_comp:
            underground_comp = UndergroundMovementComponent(entrance_comp.underground_path)
            player.add_component(underground_comp)
        else:
            underground_comp.path_points = entrance_comp.underground_path
        
        # Добавляем компонент анимации если его нет
        if not animation_comp:
            animation_comp = BurrowAnimationComponent()
            player.add_component(animation_comp)
        
        # Запускаем анимацию входа
        entrance_pos = entrance_entity.get_component(PositionComponent)
        player_pos = player.get_component(PositionComponent)
        
        animation_comp.start_animation(
            'enter_burrow',
            (player_pos.x, player_pos.y),
            (entrance_pos.x, entrance_pos.y),
            lambda entity: self._on_enter_complete(entity)
        )
    
    def _trigger_burrow_exit(self, player, exit_entity):
        """Активация выхода из норы"""
        # Проверяем, не находится ли игрок уже в процессе анимации
        animation_comp = player.get_component(BurrowAnimationComponent)
        if animation_comp and animation_comp.is_active:
            return
        
        # Добавляем компонент анимации если его нет
        if not animation_comp:
            animation_comp = BurrowAnimationComponent()
            player.add_component(animation_comp)
        
        # Запускаем анимацию выхода
        exit_pos = exit_entity.get_component(PositionComponent)
        player_pos = player.get_component(PositionComponent)
        
        animation_comp.start_animation(
            'exit_burrow',
            (player_pos.x, player_pos.y),
            (exit_pos.x, exit_pos.y),
            lambda entity: self._on_exit_complete(entity)
        )
    
    def _on_enter_complete(self, entity):
        """Завершение входа - переключение в подземный режим"""
        underground_comp = entity.get_component(UndergroundMovementComponent)
        if underground_comp:
            underground_comp.is_underground = True
    
    def _on_exit_complete(self, entity):
        """Завершение выхода - возврат в обычный режим"""
        underground_comp = entity.get_component(UndergroundMovementComponent)
        if underground_comp:
            underground_comp.is_underground = False
    
    def set_player_entity(self, player_entity):
        """Установить сущность игрока"""
        self.player_entity = player_entity
    
    def force_entrance_trigger(self, player, entrance_entity):
        """Принудительно активировать вход в нору (для ручного взаимодействия)"""
        entrance_comp = entrance_entity.get_component(BurrowEntranceComponent)
        if entrance_comp.requires_interaction:
            self._trigger_burrow_entrance(player, entrance_entity)