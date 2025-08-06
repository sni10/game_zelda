# Issue #07: Система Event Boxes и триггеров

## Описание
Реализация системы интерактивных зон (Event Boxes) для создания динамических событий в игровом мире.

## Цель
Добавить интерактивность и динамику в игровой мир через систему триггеров и событий.

## Требования

### Типы Event Boxes

#### Порталы и телепортация
- [ ] **Тайлы порталов**:
  - [ ] Специальный тип тайла с визуальными эффектами
  - [ ] Анимация портала (вращение, свечение)
  - [ ] Звуковые эффекты при активации
- [ ] **Интерактивность**:
  - [ ] Активация при наступании игрока
  - [ ] Меню выбора мира для телепортации
  - [ ] Подтверждение перехода
- [ ] **Условная активация**:
  - [ ] Требования для разблокировки портала
  - [ ] Ключевые предметы или уровень игрока
  - [ ] Выполненные квесты

#### Спаун врагов
- [ ] **Триггеры появления**:
  - [ ] Невидимые зоны на карте
  - [ ] Активация при входе игрока
  - [ ] Одноразовые и многоразовые триггеры
- [ ] **Типы спауна**:
  - [ ] Внезапное появление из "кустов"
  - [ ] Постепенное материализование
  - [ ] Выход из скрытых мест
- [ ] **Настройки спауна**:
  - [ ] Количество врагов (1-5)
  - [ ] Типы врагов
  - [ ] Уровень сложности
  - [ ] Кулдаун повторного спауна

#### Сундуки и лут
- [ ] **Сундуки с сокровищами**:
  - [ ] Визуальная модель сундука
  - [ ] Анимация открытия
  - [ ] Содержимое: предметы, золото, опыт
- [ ] **Скрытые сокровища**:
  - [ ] Невидимые до активации
  - [ ] Требуют исследования или решения головоломки
  - [ ] Редкие и ценные награды
- [ ] **Система лута**:
  - [ ] Случайная генерация содержимого
  - [ ] Уровень лута зависит от области
  - [ ] Уникальные предметы в особых сундуках

#### Активация NPC и магазинов
- [ ] **Торговцы**:
  - [ ] Появление торговца при активации
  - [ ] Временные торговцы (исчезают через время)
  - [ ] Специализированные магазины
- [ ] **Квестодатели**:
  - [ ] NPC появляются для выдачи квестов
  - [ ] Условная активация по прогрессу
  - [ ] Цепочки связанных квестов
- [ ] **Услуги**:
  - [ ] Лечение и восстановление
  - [ ] Улучшение экипировки
  - [ ] Обучение навыкам

#### Головоломки и переключатели
- [ ] **Механические переключатели**:
  - [ ] Кнопки, рычаги, плиты давления
  - [ ] Временные и постоянные эффекты
  - [ ] Комбинированные головоломки
- [ ] **Секретные проходы**:
  - [ ] Скрытые двери и стены
  - [ ] Активация по последовательности действий
  - [ ] Доступ к секретным областям
- [ ] **Логические задачи**:
  - [ ] Последовательности активации
  - [ ] Паззлы с предметами
  - [ ] Временные ограничения

#### Входы в тоннели
- [ ] **Переходы на Z-уровни**:
  - [ ] Специальные тайлы-входы
  - [ ] Плавный переход на подземный уровень
  - [ ] Визуальные эффекты погружения
- [ ] **Связь с системой Z-координат**:
  - [ ] Интеграция с Issue #02
  - [ ] Сохранение позиции при переходе
  - [ ] Корректная работа камеры

#### Сюжетные события
- [ ] **Катсцены**:
  - [ ] Автоматические диалоги
  - [ ] Движение камеры
  - [ ] Временная блокировка управления
- [ ] **Изменения мира**:
  - [ ] Появление/исчезновение объектов
  - [ ] Изменение ландшафта
  - [ ] Открытие новых областей

## Технические детали

### Архитектурные паттерны

#### ECS Components для системы событий
```python
# src/core/ecs/event_components.py
class EventBoxComponent(Component):
    """Компонент области события"""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.event_type = None
        self.parameters = {}
        self.activated = False
        self.cooldown_time = 0
        self.current_cooldown = 0
        self.one_time_only = False

class TriggerComponent(Component):
    """Компонент триггера"""
    def __init__(self, trigger_type: str):
        self.trigger_type = trigger_type  # ENTER, EXIT, INTERACT, TIMER
        self.conditions = []
        self.actions = []
        self.is_active = True

class SpawnTriggerComponent(Component):
    """Компонент спауна врагов"""
    def __init__(self, enemy_types: List[str], spawn_count: int):
        self.enemy_types = enemy_types
        self.spawn_count = spawn_count
        self.spawn_radius = 64
        self.max_spawned_entities = 5
        self.current_spawned = []
        self.respawn_time = 30000  # мс

class LootTriggerComponent(Component):
    """Компонент лута"""
    def __init__(self, loot_table: dict):
        self.loot_table = loot_table
        self.is_opened = False
        self.respawn_time = -1  # -1 = не респавнится
        self.visual_state = "closed"
```

#### Observer Pattern для системы событий
```python
# src/events/event_system.py
class EventSystem(System):
    """Система событий как центральный Observer"""
    def __init__(self):
        self._listeners = defaultdict(list)
        self._event_queue = []
    
    def subscribe(self, event_type: str, callback: Callable):
        """Подписка на события"""
        self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Отписка от событий"""
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
    
    def emit(self, event: GameEvent):
        """Отправка события"""
        self._event_queue.append(event)
    
    def process_events(self):
        """Обработка очереди событий"""
        while self._event_queue:
            event = self._event_queue.pop(0)
            for callback in self._listeners[event.type]:
                callback(event)

class EventBoxSystem(System):
    """Система обработки Event Boxes"""
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        
        # Подписка на события
        self.event_system.subscribe("player_moved", self.check_event_boxes)
        self.event_system.subscribe("player_interacted", self.handle_interaction)
    
    def check_event_boxes(self, event: PlayerMovedEvent):
        """Проверка пересечения игрока с Event Boxes"""
        player_pos = event.new_position
        
        for entity in self.get_entities_with_component(EventBoxComponent):
            event_box_comp = entity.get_component(EventBoxComponent)
            
            if event_box_comp.rect.collidepoint(player_pos):
                if not event_box_comp.activated or not event_box_comp.one_time_only:
                    self._trigger_event_box(entity, event.player)
    
    def _trigger_event_box(self, event_box_entity: Entity, player: Entity):
        """Активация Event Box"""
        event_box_comp = event_box_entity.get_component(EventBoxComponent)
        trigger_comp = event_box_entity.get_component(TriggerComponent)
        
        if trigger_comp and trigger_comp.is_active:
            # Выполнение всех действий триггера
            for action in trigger_comp.actions:
                action.execute(event_box_entity, player)
            
            event_box_comp.activated = True
            event_box_comp.current_cooldown = event_box_comp.cooldown_time
```

#### Command Pattern для действий триггеров
```python
# src/events/trigger_actions.py
class TriggerAction(ABC):
    """Базовая команда для действий триггеров"""
    
    @abstractmethod
    def execute(self, trigger_entity: Entity, player: Entity) -> bool:
        pass
    
    @abstractmethod
    def undo(self, trigger_entity: Entity, player: Entity) -> bool:
        pass

class SpawnEnemiesAction(TriggerAction):
    """Действие спауна врагов"""
    def __init__(self, enemy_factory: EnemyFactory):
        self.enemy_factory = enemy_factory
        self.spawned_entities = []
    
    def execute(self, trigger_entity: Entity, player: Entity) -> bool:
        spawn_comp = trigger_entity.get_component(SpawnTriggerComponent)
        event_box_comp = trigger_entity.get_component(EventBoxComponent)
        
        if spawn_comp and len(spawn_comp.current_spawned) < spawn_comp.max_spawned_entities:
            spawn_center = event_box_comp.rect.center
            
            for _ in range(spawn_comp.spawn_count):
                enemy_type = random.choice(spawn_comp.enemy_types)
                enemy = self.enemy_factory.create_enemy(enemy_type, 1)
                
                # Позиционирование врага
                spawn_pos = self._get_random_spawn_position(spawn_center, spawn_comp.spawn_radius)
                pos_comp = enemy.get_component(PositionComponent)
                pos_comp.x, pos_comp.y = spawn_pos
                
                spawn_comp.current_spawned.append(enemy)
                self.spawned_entities.append(enemy)
            
            return True
        return False

class OpenPortalAction(TriggerAction):
    """Действие открытия портала"""
    def __init__(self, target_world: str, target_position: tuple):
        self.target_world = target_world
        self.target_position = target_position
    
    def execute(self, trigger_entity: Entity, player: Entity) -> bool:
        # Создание портала
        portal = Entity()
        portal.add_component(PortalComponent(self.target_world, self.target_position))
        portal.add_component(PositionComponent(*trigger_entity.get_component(EventBoxComponent).rect.center))
        portal.add_component(RenderComponent("portal_sprite"))
        
        # Добавление портала в мир
        world = self._get_current_world()
        world.add_entity(portal)
        
        return True

class GiveLootAction(TriggerAction):
    """Действие выдачи лута"""
    def __init__(self, item_factory: ItemFactory):
        self.item_factory = item_factory
        self.given_items = []
    
    def execute(self, trigger_entity: Entity, player: Entity) -> bool:
        loot_comp = trigger_entity.get_component(LootTriggerComponent)
        
        if loot_comp and not loot_comp.is_opened:
            # Генерация лута по таблице
            generated_items = self._generate_loot(loot_comp.loot_table)
            
            # Добавление предметов в инвентарь игрока
            inventory_comp = player.get_component(InventoryComponent)
            for item in generated_items:
                if inventory_comp.add_item(item):
                    self.given_items.append(item)
            
            loot_comp.is_opened = True
            loot_comp.visual_state = "opened"
            
            return True
        return False

class ActivateNPCAction(TriggerAction):
    """Действие активации NPC"""
    def __init__(self, npc_factory: NPCFactory):
        self.npc_factory = npc_factory
        self.spawned_npc = None
    
    def execute(self, trigger_entity: Entity, player: Entity) -> bool:
        if not self.spawned_npc:
            # Создание NPC
            npc_type = trigger_entity.get_component(EventBoxComponent).parameters.get("npc_type", "merchant")
            self.spawned_npc = self.npc_factory.create_npc(npc_type, 1)
            
            # Позиционирование NPC
            spawn_pos = trigger_entity.get_component(EventBoxComponent).rect.center
            pos_comp = self.spawned_npc.get_component(PositionComponent)
            pos_comp.x, pos_comp.y = spawn_pos
            
            # Добавление в мир
            world = self._get_current_world()
            world.add_entity(self.spawned_npc)
            
            return True
        return False
```

#### Factory Pattern для создания Event Boxes
```python
# src/events/event_box_factory.py
class EventBoxFactory(ABC):
    """Абстрактная фабрика для создания Event Boxes"""
    
    @abstractmethod
    def create_event_box(self, event_type: str, parameters: dict) -> Entity:
        pass

class StandardEventBoxFactory(EventBoxFactory):
    """Стандартная фабрика Event Boxes"""
    def __init__(self, item_factory: ItemFactory, enemy_factory: EnemyFactory, npc_factory: NPCFactory):
        self.item_factory = item_factory
        self.enemy_factory = enemy_factory
        self.npc_factory = npc_factory
    
    def create_event_box(self, event_type: str, parameters: dict) -> Entity:
        entity = Entity()
        
        # Базовые компоненты
        entity.add_component(EventBoxComponent(
            parameters['x'], parameters['y'],
            parameters['width'], parameters['height']
        ))
        
        trigger_comp = TriggerComponent(parameters.get('trigger_type', 'ENTER'))
        
        # Создание действий в зависимости от типа события
        if event_type == "spawn_enemies":
            entity.add_component(SpawnTriggerComponent(
                parameters['enemy_types'],
                parameters['spawn_count']
            ))
            trigger_comp.actions.append(SpawnEnemiesAction(self.enemy_factory))
        
        elif event_type == "loot_chest":
            entity.add_component(LootTriggerComponent(parameters['loot_table']))
            trigger_comp.actions.append(GiveLootAction(self.item_factory))
        
        elif event_type == "portal":
            trigger_comp.actions.append(OpenPortalAction(
                parameters['target_world'],
                parameters['target_position']
            ))
        
        elif event_type == "activate_npc":
            trigger_comp.actions.append(ActivateNPCAction(self.npc_factory))
        
        entity.add_component(trigger_comp)
        return entity

class WorldSpecificEventBoxFactory(EventBoxFactory):
    """Фабрика Event Boxes для конкретного мира"""
    def __init__(self, world_type: str, base_factory: StandardEventBoxFactory):
        self.world_type = world_type
        self.base_factory = base_factory
    
    def create_event_box(self, event_type: str, parameters: dict) -> Entity:
        # Модификация параметров в зависимости от мира
        if self.world_type == "ice_world":
            parameters = self._apply_ice_world_modifiers(parameters)
        elif self.world_type == "fire_world":
            parameters = self._apply_fire_world_modifiers(parameters)
        
        return self.base_factory.create_event_box(event_type, parameters)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── event_components.py       # Компоненты событий
├── events/
│   ├── event_system.py           # Система событий (Observer Pattern)
│   ├── event_box_system.py       # Система Event Boxes (ECS System)
│   ├── trigger_actions.py        # Действия триггеров (Command Pattern)
│   ├── event_box_factory.py      # Фабрика Event Boxes (Factory Pattern)
│   └── game_events.py            # Определения игровых событий
├── world/
│   ├── event_loader.py           # Загрузка событий из конфигурации
│   └── world_events.py           # События мира
└── ui/
    └── event_notifications.py    # Уведомления о событиях
```

### Файлы для создания/изменения
- `src/core/ecs/event_components.py` - компоненты событий
- `src/events/event_system.py` - система событий (Observer Pattern)
- `src/events/event_box_system.py` - система Event Boxes (ECS System)
- `src/events/trigger_actions.py` - действия триггеров (Command Pattern)
- `src/events/event_box_factory.py` - фабрика Event Boxes (Factory Pattern)
- `src/events/game_events.py` - определения игровых событий
- `src/world/event_loader.py` - загрузка событий из конфигурации
- `src/ui/event_notifications.py` - уведомления о событиях
- `src/world/world.py` - интеграция с миром

### Архитектура системы событий
```python
class EventBox:
    def __init__(self, x, y, width, height, event_type, parameters):
        self.rect = pygame.Rect(x, y, width, height)
        self.event_type = event_type
        self.parameters = parameters
        self.activated = False
        self.cooldown = 0
        
    def check_trigger(self, player_pos):
        if self.rect.collidepoint(player_pos):
            self.activate()
            
    def activate(self):
        # Выполнение события в зависимости от типа
        pass

class EventSystem:
    def __init__(self):
        self.event_boxes = []
        
    def update(self, dt, player_pos):
        for event_box in self.event_boxes:
            event_box.check_trigger(player_pos)
```

### Конфигурация событий
```ini
[EVENT_SYSTEM]
max_events_per_frame = 5
default_cooldown = 1000
portal_activation_delay = 500

[SPAWN_EVENTS]
max_enemies_per_spawn = 5
spawn_radius = 64
despawn_distance = 300

[LOOT_EVENTS]
common_loot_chance = 70
rare_loot_chance = 25
epic_loot_chance = 5
```

### Интеграция с другими системами
- [ ] **Система миров**: порталы для телепортации
- [ ] **Система врагов**: спаун и управление
- [ ] **Система предметов**: генерация лута
- [ ] **Квестовая система**: активация квестов
- [ ] **Z-координаты**: входы в тоннели
- [ ] **Система сохранений**: состояние событий

### Редактор событий (опционально)
- [ ] **Визуальный редактор**:
  - [ ] Размещение Event Boxes на карте
  - [ ] Настройка параметров событий
  - [ ] Предпросмотр зон активации
- [ ] **Файловый формат**:
  - [ ] JSON конфигурация событий
  - [ ] Загрузка событий для каждого мира
  - [ ] Валидация параметров

## Критерии готовности
- [ ] Минимум 6 типов Event Boxes реализованы
- [ ] События корректно активируются при взаимодействии
- [ ] Система не влияет на производительность
- [ ] События сохраняют состояние между сессиями
- [ ] Визуальные и звуковые эффекты работают
- [ ] Интеграция с другими системами функциональна

## Приоритет
**Высокий** - Критически важно для интерактивности мира

## Зависимости
- Issue #01 (Множественные миры) - для порталов
- Issue #02 (Z-координаты) - для входов в тоннели
- Issue #05 (Враги) - для спауна
- Issue #08 (Инвентарь) - для лута
- Issue #09 (Квесты) - для квестовых событий

## Тестирование
- [ ] Тестовая карта с различными типами событий
- [ ] Проверка производительности при множественных событиях
- [ ] Тестирование сохранения состояния
- [ ] Проверка интеграции с другими системами

## Примерное время реализации
3-4 недели

## Связанные issues
- #01 (Множественные миры) - порталы
- #02 (Z-координаты) - тоннели
- #05 (Враги) - спаун
- #08 (Инвентарь) - лут
- #09 (Квесты) - квестовые события