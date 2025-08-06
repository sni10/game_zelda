# Issue #01: Система множественных миров и телепортации

## Описание
Реализация системы множественных миров с порталами для телепортации между различными локациями игры.

## Цель
Расширить игровой мир за пределы одной карты, добавив возможность путешествий между различными тематическими мирами.

## Требования

### Основная функциональность
- [ ] Создание системы множественных карт различных размеров
- [ ] Реализация тайлов-порталов с визуальными эффектами (радужное переливание градиента)
- [ ] Интерактивная система выбора мира для телепортации (путем активации карты в инвентаре открывается список локаций)
- [ ] Двусторонние порталы для возврата в исходный мир
- [ ] Сохранение состояния каждого мира отдельно

### Типы миров для реализации
- [ ] **Основной мир**: стартовая локация 2000x2000 (уже существует)
- [ ] **Мир-пещера**: горы + травяные поля + тоннели
- [ ] **Подземный мир**: лава, особые враги, высокая сложность
- [ ] **Ледяной мир**: заснеженный ландшафт, эффект скольжения
- [ ] **Лесной мир**: густой лес, скрытые тропы

### Экраны загрузки
- [ ] Красивые заставки для каждого мира
- [ ] Интерактивное повествование по частям
- [ ] Прогрессивная история при переходах
- [ ] Фоновая музыка для каждого мира

## Технические детали

### Архитектурные паттерны

#### Abstract Factory Pattern для создания миров
```python
# src/factories/world_factory.py
from abc import ABC, abstractmethod

class WorldFactory(ABC):
    """Абстрактная фабрика для создания различных типов миров"""
    
    @abstractmethod
    def create_world(self, world_id: str, size: tuple) -> World:
        pass
    
    @abstractmethod
    def create_entities(self, world: World) -> List[Entity]:
        pass
    
    @abstractmethod
    def create_portals(self, world: World) -> List[Portal]:
        pass

class MainWorldFactory(WorldFactory):
    """Фабрика для основного мира"""
    def create_world(self, world_id: str, size: tuple) -> World:
        world = World(world_id, size)
        world.add_component(TerrainComponent("grass_plains"))
        world.add_component(WeatherComponent("sunny"))
        return world
    
    def create_entities(self, world: World) -> List[Entity]:
        entities = []
        # Создание NPC торговцев, квестодателей
        merchant = self.entity_factory.create_npc("merchant", 1)
        entities.append(merchant)
        return entities

class CaveWorldFactory(WorldFactory):
    """Фабрика для мира-пещеры с тоннелями"""
    def create_world(self, world_id: str, size: tuple) -> World:
        world = World(world_id, size)
        world.add_component(TerrainComponent("cave_mountains"))
        world.add_component(TunnelSystemComponent())
        return world
```

#### ECS Components для миров
```python
# src/core/ecs/world_components.py
class WorldComponent(Component):
    """Базовый компонент мира"""
    pass

class TerrainComponent(WorldComponent):
    def __init__(self, terrain_type: str):
        self.terrain_type = terrain_type
        self.tile_set = self._load_tileset(terrain_type)

class PortalComponent(Component):
    """Компонент портала для телепортации"""
    def __init__(self, target_world: str, target_position: tuple):
        self.target_world = target_world
        self.target_position = target_position
        self.activation_requirements = []
        self.visual_effects = []

class LoadingScreenComponent(Component):
    """Компонент экрана загрузки для мира"""
    def __init__(self, background_image: str, story_text: str):
        self.background_image = background_image
        self.story_text = story_text
        self.music_track = None
```

#### Observer Pattern для событий миров
```python
# src/events/world_events.py
class WorldEvent(GameEvent):
    def __init__(self, world_id: str):
        super().__init__("world_event")
        self.world_id = world_id

class WorldLoadedEvent(WorldEvent):
    def __init__(self, world_id: str, world: World):
        super().__init__(world_id)
        self.world = world

class PortalActivatedEvent(WorldEvent):
    def __init__(self, world_id: str, portal: Entity, player: Entity):
        super().__init__(world_id)
        self.portal = portal
        self.player = player

# Использование в системе
class WorldSystem(System):
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        self.event_system.subscribe("portal_activated", self.handle_portal_activation)
    
    def handle_portal_activation(self, event: PortalActivatedEvent):
        # Логика телепортации между мирами
        self.teleport_player(event.player, event.portal.target_world)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── factories/
│   ├── world_factory.py          # Фабрики миров
│   └── entity_factory.py         # Фабрики сущностей
├── world/
│   ├── world_manager.py          # Управление множественными мирами
│   ├── portal_system.py          # Система порталов (ECS System)
│   └── loading_system.py         # Система загрузки миров
├── core/ecs/
│   ├── world_components.py       # Компоненты для миров
│   └── portal_components.py      # Компоненты порталов
└── events/
    └── world_events.py           # События миров
```

### Файлы для создания/изменения
- `src/factories/world_factory.py` - фабрики для создания миров
- `src/world/world_manager.py` - управление множественными мирами (ECS System)
- `src/world/portal_system.py` - система порталов (ECS System)
- `src/ui/loading_screen.py` - экраны загрузки
- `src/core/ecs/world_components.py` - компоненты миров
- `src/events/world_events.py` - события миров
- `config.ini` - настройки миров

### Интеграция с существующими системами
- **ECS интеграция**: Миры становятся сущностями с компонентами
- **Event System**: Все переходы между мирами через события
- **Save System**: Использование Memento Pattern для сохранения состояния миров
- **Factory Pattern**: Изолированное создание различных типов миров

## Критерии готовности
- [ ] Игрок может телепортироваться между минимум 3 мирами
- [ ] Состояние каждого мира сохраняется независимо
- [ ] Экраны загрузки показывают уникальный контент
- [ ] Порталы имеют визуальные эффекты и интерактивность
- [ ] Система работает стабильно без утечек памяти

## Приоритет
**Высокий** - Базовая функциональность для дальнейшего расширения

## Зависимости
- Текущая система мира (World)
- Система сохранений (SaveSystem)
- Система конфигурации

## Примерное время реализации
2-3 недели

## Связанные issues
- #02 (Z-координата и тоннели)
- #07 (Event boxes и триггеры)