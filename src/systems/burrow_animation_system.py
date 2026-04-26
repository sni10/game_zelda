"""
Система анимаций для механики нор (burrow mechanics)
"""
from src.core.ecs.system import System
from src.core.ecs.component import PositionComponent
from src.components.burrow_components import BurrowAnimationComponent


class BurrowAnimationSystem(System):
    """Система анимаций заползания/выползания"""
    
    def __init__(self, entity_manager):
        super().__init__(entity_manager)
        self.active_animations = {}
    
    def get_required_components(self):
        return [BurrowAnimationComponent, PositionComponent]
    
    def update(self, dt: float):
        """Обновление анимаций"""
        for entity in self.get_entities():
            animation_comp = entity.get_component(BurrowAnimationComponent)
            pos_comp = entity.get_component(PositionComponent)
            
            if animation_comp.is_active:
                # Обновляем анимацию
                animation_complete = animation_comp.update(dt)
                
                # Обновляем позицию сущности
                current_pos = animation_comp.get_current_position()
                if current_pos:
                    pos_comp.x, pos_comp.y = current_pos
                
                # Если анимация завершена, выполняем callback
                if animation_complete and animation_comp.callback:
                    animation_comp.callback(entity)