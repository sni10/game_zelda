"""
Компоненты для механики нор (burrow mechanics) в стиле Zelda: Ocarina of Time 2D
"""
from src.core.ecs.component import Component


class BurrowEntranceComponent(Component):
    """Компонент входа в нору"""
    def __init__(self, exit_position: tuple, underground_path: list):
        self.exit_position = exit_position  # Координаты выхода
        self.underground_path = underground_path  # Точки подземного пути
        self.is_active = True
        self.requires_interaction = False  # Автоматический или ручной вход


class BurrowExitComponent(Component):
    """Компонент выхода из норы"""
    def __init__(self, entrance_position: tuple):
        self.entrance_position = entrance_position
        self.is_active = True


class UndergroundMovementComponent(Component):
    """Компонент для движения под землей"""
    def __init__(self, path_points: list, current_point: int = 0):
        self.path_points = path_points  # Список точек пути
        self.current_point = current_point
        self.is_underground = False
        self.movement_speed = 0.8  # Замедленное движение под землей


class HillSurfaceComponent(Component):
    """Компонент поверхности холма"""
    def __init__(self, surface_entities: list):
        self.surface_entities = surface_entities  # Коровы и другие объекты
        self.underground_area = None  # Область под холмом


class BurrowAnimationComponent(Component):
    """Компонент для анимаций заползания/выползания"""
    def __init__(self):
        self.animation_type = None  # 'enter_burrow' или 'exit_burrow'
        self.start_pos = None
        self.target_pos = None
        self.duration = 1000  # Длительность анимации в миллисекундах
        self.current_time = 0
        self.is_active = False
        self.callback = None
        
    def start_animation(self, animation_type: str, start_pos: tuple, target_pos: tuple, callback=None):
        """Запустить анимацию"""
        self.animation_type = animation_type
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.current_time = 0
        self.is_active = True
        self.callback = callback
        
    def update(self, dt: float):
        """Обновить анимацию"""
        if not self.is_active:
            return False
            
        self.current_time += dt
        progress = min(self.current_time / self.duration, 1.0)
        
        if progress >= 1.0:
            self.is_active = False
            if self.callback:
                self.callback()
            return True
            
        return False
        
    def get_current_position(self):
        """Получить текущую позицию в анимации"""
        if not self.is_active or not self.start_pos or not self.target_pos:
            return None
            
        progress = min(self.current_time / self.duration, 1.0)
        
        # Линейная интерполяция между начальной и конечной позицией
        x = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * progress
        y = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * progress
        
        return (x, y)


class TriggerComponent(Component):
    """Базовый компонент для триггеров"""
    def __init__(self, trigger_type: str, activation_radius: float = 16.0):
        self.trigger_type = trigger_type  # 'button', 'quest', 'dialogue', etc.
        self.activation_radius = activation_radius
        self.is_active = True
        self.cooldown = 0
        self.activation_count = 0
        self.max_activations = -1  # -1 для неограниченного количества активаций
        
    def can_activate(self):
        """Проверить, можно ли активировать триггер"""
        return (self.is_active and 
                self.cooldown <= 0 and 
                (self.max_activations == -1 or self.activation_count < self.max_activations))
                
    def activate(self, cooldown_ms: int = 1000):
        """Активировать триггер"""
        if self.can_activate():
            self.activation_count += 1
            self.cooldown = cooldown_ms
            return True
        return False
        
    def update(self, dt: float):
        """Обновить состояние триггера"""
        if self.cooldown > 0:
            self.cooldown -= dt


class NPCSpawnComponent(Component):
    """Компонент для точек появления NPC"""
    def __init__(self, npc_type: str, spawn_conditions: dict = None):
        self.npc_type = npc_type
        self.spawn_conditions = spawn_conditions or {}
        self.spawned_entity = None
        self.is_spawned = False
        self.respawn_time = -1  # -1 для отсутствия респавна
        self.last_spawn_time = 0
        
    def can_spawn(self):
        """Проверить, можно ли заспавнить NPC"""
        return not self.is_spawned
        
    def spawn_npc(self, entity_id: int):
        """Заспавнить NPC"""
        self.spawned_entity = entity_id
        self.is_spawned = True
        self.last_spawn_time = 0
        
    def despawn_npc(self):
        """Деспавнить NPC"""
        self.spawned_entity = None
        self.is_spawned = False


class DialogueZoneComponent(Component):
    """Компонент для зон диалога"""
    def __init__(self, dialogue_id: str, activation_radius: float = 32.0):
        self.dialogue_id = dialogue_id
        self.activation_radius = activation_radius
        self.is_active = True
        self.auto_trigger = True  # Автоматически запускать диалог при входе в зону
        self.dialogue_completed = False
        
    def start_dialogue(self):
        """Запустить диалог"""
        if self.is_active and not self.dialogue_completed:
            return True
        return False
        
    def complete_dialogue(self):
        """Завершить диалог"""
        self.dialogue_completed = True