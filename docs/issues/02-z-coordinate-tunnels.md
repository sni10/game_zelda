# Issue #02: Система Z-координат и тоннелей

## Описание
Реализация системы высоты (Z-координата) для создания многослойного ландшафта с тоннелями, мостами и многоуровневыми структурами.

## Цель
Добавить третье измерение в 2D игру для создания более сложной и интересной геометрии мира с возможностью движения на разных уровнях высоты.

## Требования

### Система Z-координат
- [ ] Введение Z-координаты для всех игровых объектов
- [ ] Три основных Z-уровня:
  - [ ] Z = -1: подземные тоннели, подвалы
  - [ ] Z = 0: базовый уровень игры (текущий)
  - [ ] Z = +1: мосты, верхушки деревьев, крыши
- [ ] Система рендеринга по слоям с правильной сортировкой
- [ ] Визуальные эффекты глубины и перекрытия

### Система тоннелей
- [ ] **Входы в тоннели**: специальные тайлы-триггеры
- [ ] **Структура тоннелей**:
  - [ ] Длина: от 2 до 5 клеток
  - [ ] Ширина: 2 клетки (узкий проход)
  - [ ] Стены: ограничения движения по бокам
- [ ] **Визуальное перекрытие**: травяные тайлы скрывают игрока в тоннеле
- [ ] **Выходы из тоннелей**: возврат на базовый уровень

### Расширенная механика высоты
- [ ] **Мосты**: движение над и под структурами
- [ ] **Многоуровневые здания**: лестницы между этажами
- [ ] **Водопады и обрывы**: визуальные эффекты глубины
- [ ] **Летающие объекты**: существа на разных Z-уровнях

## Технические детали

### Архитектурные паттерны

#### ECS Components для Z-координат
```python
# src/core/ecs/spatial_components.py
class PositionComponent(Component):
    """Расширенный компонент позиции с Z-координатой"""
    def __init__(self, x: float, y: float, z: int = 0):
        self.x = x
        self.y = y
        self.z = z  # -1: подземный, 0: базовый, +1: надземный
        self.previous_z = z

class ZLevelComponent(Component):
    """Компонент для управления Z-уровнями"""
    def __init__(self, current_level: int = 0):
        self.current_level = current_level
        self.can_change_levels = True
        self.transition_cooldown = 0

class TunnelComponent(Component):
    """Компонент тоннеля"""
    def __init__(self, entrance_pos: tuple, exit_pos: tuple, length: int):
        self.entrance_pos = entrance_pos
        self.exit_pos = exit_pos
        self.length = length
        self.width = 2  # клетки
        self.tunnel_path = self._generate_path()

class RenderLayerComponent(Component):
    """Компонент для рендеринга по слоям"""
    def __init__(self, layer: int, alpha: int = 255):
        self.layer = layer
        self.alpha = alpha  # для эффектов перекрытия
        self.visible = True
```

#### Strategy Pattern для рендеринга слоев
```python
# src/rendering/layer_strategies.py
class LayerRenderStrategy(ABC):
    """Стратегия рендеринга для разных Z-уровней"""
    
    @abstractmethod
    def render(self, entity: Entity, screen: Surface, camera_offset: tuple):
        pass

class UndergroundRenderStrategy(LayerRenderStrategy):
    """Рендеринг подземного уровня (Z = -1)"""
    def render(self, entity: Entity, screen: Surface, camera_offset: tuple):
        # Затемненный рендеринг для подземелий
        render_comp = entity.get_component(RenderComponent)
        pos_comp = entity.get_component(PositionComponent)
        
        if pos_comp.z == -1:
            # Рендерим с затемнением
            darkened_surface = self._apply_darkness(render_comp.sprite)
            screen.blit(darkened_surface, (pos_comp.x - camera_offset[0], 
                                         pos_comp.y - camera_offset[1]))

class OverlayRenderStrategy(LayerRenderStrategy):
    """Рендеринг перекрывающих объектов (трава над тоннелями)"""
    def render(self, entity: Entity, screen: Surface, camera_offset: tuple):
        # Полупрозрачный рендеринг для перекрытий
        render_comp = entity.get_component(RenderComponent)
        layer_comp = entity.get_component(RenderLayerComponent)
        
        if layer_comp.alpha < 255:
            overlay_surface = render_comp.sprite.copy()
            overlay_surface.set_alpha(layer_comp.alpha)
            screen.blit(overlay_surface, position)

class LayerRenderer(System):
    """Система рендеринга по слоям"""
    def __init__(self):
        self.strategies = {
            -1: UndergroundRenderStrategy(),
            0: BaseRenderStrategy(),
            1: ElevatedRenderStrategy()
        }
    
    def update(self, dt: float, entities: List[Entity]):
        # Сортировка по Z-уровню для правильного порядка рендеринга
        sorted_entities = sorted(entities, 
                               key=lambda e: e.get_component(PositionComponent).z)
        
        for entity in sorted_entities:
            pos_comp = entity.get_component(PositionComponent)
            strategy = self.strategies.get(pos_comp.z)
            if strategy:
                strategy.render(entity, self.screen, self.camera_offset)
```

#### State Pattern для переходов между Z-уровнями
```python
# src/world/z_transition_states.py
class ZTransitionState(ABC):
    """Состояние перехода между Z-уровнями"""
    
    @abstractmethod
    def handle_transition(self, entity: Entity, target_z: int) -> bool:
        pass

class EnteringTunnelState(ZTransitionState):
    """Состояние входа в тоннель"""
    def handle_transition(self, entity: Entity, target_z: int) -> bool:
        pos_comp = entity.get_component(PositionComponent)
        z_comp = entity.get_component(ZLevelComponent)
        
        if target_z == -1 and pos_comp.z == 0:
            # Анимация погружения
            self._play_enter_animation(entity)
            pos_comp.z = -1
            z_comp.current_level = -1
            return True
        return False

class ExitingTunnelState(ZTransitionState):
    """Состояние выхода из тоннеля"""
    def handle_transition(self, entity: Entity, target_z: int) -> bool:
        pos_comp = entity.get_component(PositionComponent)
        
        if target_z == 0 and pos_comp.z == -1:
            # Анимация всплытия
            self._play_exit_animation(entity)
            pos_comp.z = 0
            return True
        return False

class ZTransitionSystem(System):
    """Система управления переходами между Z-уровнями"""
    def __init__(self):
        self.states = {
            'entering_tunnel': EnteringTunnelState(),
            'exiting_tunnel': ExitingTunnelState(),
            'climbing_bridge': ClimbingBridgeState()
        }
```

#### Observer Pattern для Z-событий
```python
# src/events/z_level_events.py
class ZLevelChangedEvent(GameEvent):
    """Событие изменения Z-уровня"""
    def __init__(self, entity: Entity, old_z: int, new_z: int):
        super().__init__("z_level_changed")
        self.entity = entity
        self.old_z = old_z
        self.new_z = new_z

class TunnelEnteredEvent(GameEvent):
    """Событие входа в тоннель"""
    def __init__(self, entity: Entity, tunnel: Entity):
        super().__init__("tunnel_entered")
        self.entity = entity
        self.tunnel = tunnel

# Использование в системах
class CollisionSystem(System):
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
    
    def check_z_collision(self, entity1: Entity, entity2: Entity) -> bool:
        pos1 = entity1.get_component(PositionComponent)
        pos2 = entity2.get_component(PositionComponent)
        
        # Коллизия только на одном Z-уровне
        return pos1.z == pos2.z and self._check_2d_collision(entity1, entity2)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   ├── spatial_components.py     # Компоненты позиции и Z-уровней
│   └── render_components.py      # Компоненты рендеринга
├── rendering/
│   ├── layer_strategies.py       # Стратегии рендеринга слоев
│   ├── layer_renderer.py         # Система рендеринга по слоям
│   └── z_effects.py              # Визуальные эффекты для Z-переходов
├── world/
│   ├── z_level_manager.py        # Управление Z-уровнями (ECS System)
│   ├── tunnel_system.py          # Система тоннелей (ECS System)
│   └── z_transition_states.py    # Состояния переходов между уровнями
└── events/
    └── z_level_events.py         # События Z-уровней
```

### Файлы для создания/изменения
- `src/core/ecs/spatial_components.py` - компоненты позиции с Z-координатой
- `src/rendering/layer_strategies.py` - стратегии рендеринга слоев
- `src/rendering/layer_renderer.py` - система рендеринга по слоям (ECS System)
- `src/world/z_level_manager.py` - управление Z-уровнями (ECS System)
- `src/world/tunnel_system.py` - система тоннелей (ECS System)
- `src/world/z_transition_states.py` - состояния переходов
- `src/events/z_level_events.py` - события Z-уровней
- `src/entities/player.py` - добавление Z-компонентов игроку

### Интеграция с существующими системами
- **ECS интеграция**: Все объекты получают PositionComponent с Z-координатой
- **Strategy Pattern**: Различные стратегии рендеринга для каждого Z-уровня
- **State Pattern**: Управление переходами между уровнями через состояния
- **Observer Pattern**: События для синхронизации систем при смене Z-уровня

### Конфигурация
```ini
[Z_LEVELS]
min_z = -1
max_z = 1
tunnel_max_length = 5
tunnel_width = 2
overlay_alpha = 128
```

## Пример реализации для мира-пещеры

### Структура мира-пещеры
- [ ] Карта окружена горами (естественные границы)
- [ ] Внутри травяные поля (базовый Z-уровень 0)
- [ ] **3 тоннеля разной длины**:
  - [ ] Короткий (2 клетки): простой проход
  - [ ] Средний (3-4 клетки): с поворотом
  - [ ] Длинный (5 клеток): прямой, с сокровищем в середине

## Критерии готовности
- [ ] Игрок может входить и выходить из тоннелей
- [ ] Визуальное перекрытие работает корректно
- [ ] Коллизии учитывают Z-координату
- [ ] Рендеринг слоев работает без артефактов
- [ ] Система сохраняет Z-позицию игрока
- [ ] Производительность остается стабильной (60 FPS)

## Приоритет
**Высокий** - Критически важно для реализации сложной геометрии мира

## Зависимости
- Issue #01 (Множественные миры) - для тестирования в мире-пещере
- Текущая система рендеринга
- Система коллизий

## Риски и сложности
- Сложность рендеринга многослойных объектов
- Возможные проблемы с производительностью
- Необходимость переработки существующей системы координат

## Примерное время реализации
3-4 недели

## Связанные issues
- #01 (Множественные миры)
- #07 (Event boxes и триггеры)
- #08 (Расширенная боевая система)