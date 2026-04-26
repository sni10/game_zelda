"""
Система движения по подземным тропинкам
"""
import math
from src.core.ecs.system import System
from src.core.ecs.component import PositionComponent
from src.components.burrow_components import UndergroundMovementComponent, BurrowExitComponent


class UndergroundMovementSystem(System):
    """Система движения по подземным тропинкам"""
    
    def __init__(self, entity_manager):
        super().__init__(entity_manager)
    
    def get_required_components(self):
        return [UndergroundMovementComponent, PositionComponent]
    
    def update(self, dt: float):
        """Обновление движения под землей"""
        for entity in self.get_entities():
            underground_comp = entity.get_component(UndergroundMovementComponent)
            pos_comp = entity.get_component(PositionComponent)
            
            if underground_comp.is_underground:
                # Ограничиваем движение только по тропинке
                self._constrain_to_path(pos_comp, underground_comp)
                
                # Проверяем достижение выхода
                if self._reached_exit(pos_comp, underground_comp):
                    self._trigger_exit(entity)
    
    def _constrain_to_path(self, pos_comp, underground_comp):
        """Ограничение движения по подземной тропинке"""
        if not underground_comp.path_points:
            return
            
        # Находим ближайшую точку на тропинке
        closest_point = self._find_closest_path_point(
            (pos_comp.x, pos_comp.y), 
            underground_comp.path_points
        )
        
        # Корректируем позицию если игрок отклонился
        max_deviation = 16  # Максимальное отклонение от тропинки
        distance = self._distance_to_point((pos_comp.x, pos_comp.y), closest_point)
        
        if distance > max_deviation:
            # Возвращаем на тропинку
            pos_comp.x, pos_comp.y = closest_point
    
    def _find_closest_path_point(self, current_pos, path_points):
        """Найти ближайшую точку на тропинке"""
        if not path_points:
            return current_pos
            
        closest_point = path_points[0]
        min_distance = self._distance_to_point(current_pos, closest_point)
        
        for point in path_points[1:]:
            distance = self._distance_to_point(current_pos, point)
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        return closest_point
    
    def _distance_to_point(self, pos1, pos2):
        """Вычислить расстояние между двумя точками"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _reached_exit(self, pos_comp, underground_comp):
        """Проверить, достиг ли игрок выхода"""
        if not underground_comp.path_points:
            return False
            
        # Проверяем близость к последней точке пути (выходу)
        exit_point = underground_comp.path_points[-1]
        distance = self._distance_to_point((pos_comp.x, pos_comp.y), exit_point)
        
        return distance <= 16  # Радиус активации выхода
    
    def _trigger_exit(self, entity):
        """Активировать выход из норы"""
        # Найти ближайший выход
        for exit_entity in self.entity_manager.get_entities_with_component(BurrowExitComponent):
            exit_pos = exit_entity.get_component(PositionComponent)
            entity_pos = entity.get_component(PositionComponent)
            
            if self._distance_to_point((entity_pos.x, entity_pos.y), (exit_pos.x, exit_pos.y)) <= 32:
                # Запускаем процесс выхода из норы
                underground_comp = entity.get_component(UndergroundMovementComponent)
                underground_comp.is_underground = False
                break
    
    def start_underground_movement(self, entity, path_points):
        """Начать движение под землей"""
        underground_comp = entity.get_component(UndergroundMovementComponent)
        if underground_comp:
            underground_comp.path_points = path_points
            underground_comp.is_underground = True
            underground_comp.current_point = 0
    
    def stop_underground_movement(self, entity):
        """Остановить движение под землей"""
        underground_comp = entity.get_component(UndergroundMovementComponent)
        if underground_comp:
            underground_comp.is_underground = False