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

---

## Подзадачи для реализации

### 🏗️ Фаза 1: Архитектурная подготовка
**Цель**: Создание базовой архитектуры для поддержки множественных миров

#### 1.1 Рефакторинг системы координат
- [ ] Обновить `src/entities/player.py` для поддержки world_id
- [ ] Обновить `src/world/world.py` для поддержки world_id  
- [ ] Обновить `src/core/game.py` для поддержки world_id
- [ ] Создать `test_world_coordinates.py` - unit тесты координат в разных мирах
- [ ] Все существующие тесты проходят с новой системой координат

#### 1.2 Создание базовых компонентов ECS
- [ ] Создать `src/core/ecs/world_components.py` - WorldComponent, LoadingScreenComponent
- [ ] Создать `src/core/ecs/portal_components.py` - PortalComponent
- [ ] Создать `test_world_components.py` - unit тесты всех компонентов ECS
- [ ] 100% покрытие тестами всех компонентов

#### 1.3 Событийная система для миров
- [ ] Создать `src/events/world_events.py` - WorldEvent, WorldLoadedEvent, PortalActivatedEvent
- [ ] Создать `test_world_events.py` - тестирование событий
- [ ] События корректно обрабатываются подписчиками

### 🏭 Фаза 2: Фабричные паттерны
**Цель**: Создание системы для генерации различных типов миров

#### 2.1 Abstract Factory Pattern
- [ ] Создать `src/factories/world_factory.py` - базовый WorldFactory
- [ ] Создать `test_world_factory.py` - тестирование создания всех типов миров
- [ ] Каждая фабрика создает корректный мир с валидными компонентами

#### 2.2 Конкретные фабрики миров
- [ ] Создать MainWorldFactory в `src/factories/specific_world_factories.py`
- [ ] Создать CaveWorldFactory
- [ ] Создать UndergroundWorldFactory
- [ ] Создать IceWorldFactory
- [ ] Создать ForestWorldFactory
- [ ] Создать `test_specific_factories.py` - unit тесты каждой фабрики
- [ ] Все 5 типов миров генерируются с уникальными характеристиками

### 🌐 Фаза 3: Система управления мирами
**Цель**: Core-функциональность для работы с множественными мирами

#### 3.1 WorldManager как ECS System
- [ ] Создать `src/world/world_manager.py` - управление загрузкой/выгрузкой миров
- [ ] Создать `test_world_manager.py` - тестирование переключения между мирами
- [ ] Переключение между мирами без потери данных и утечек памяти

#### 3.2 Система порталов как ECS System
- [ ] Создать `src/world/portal_system.py` - PortalSystem для взаимодействий с порталами
- [ ] Создать `test_portal_system.py` - тестирование активации и телепортации
- [ ] Игрок корректно телепортируется при взаимодействии с порталом

#### 3.3 Система сохранения состояния миров
- [ ] Расширить `src/systems/save_system.py` для поддержки множественных миров
- [ ] Создать `test_multiworld_saves.py` - тестирование сохранения/загрузки всех миров
- [ ] Состояние каждого мира сохраняется и загружается независимо

### 🎨 Фаза 4: Пользовательский интерфейс и визуализация
**Цель**: Создание UI для работы с мирами и визуальных эффектов

#### 4.1 Экраны загрузки миров
- [ ] Создать `src/ui/loading_screen.py` - LoadingScreen с прогрессивным повествованием
- [ ] Создать `test_loading_screen.py` - тестирование отображения контента
- [ ] Уникальные экраны загрузки для каждого мира с историей

#### 4.2 Визуальные эффекты порталов
- [ ] Создать `src/rendering/portal_effects.py` - анимации и эффекты тайлов-порталов
- [ ] Создать `test_portal_rendering.py` - тестирование отрисовки эффектов
- [ ] Порталы имеют привлекательные визуальные эффекты

#### 4.3 UI для выбора миров
- [ ] Создать `src/ui/world_selection.py` - интерфейс выбора мира
- [ ] Создать `test_world_selection_ui.py` - тестирование навигации и выбора
- [ ] Удобный интерфейс для выбора доступных миров

### 🌍 Фаза 5: Создание контента миров
**Цель**: Реализация каждого типа мира с уникальными особенностями

#### 5.1 Мир-пещера (приоритет для тестирования тоннелей)
- [ ] Создать `data/worlds/cave_world.txt` - мир с горами, травяными полями и входами в тоннели
- [ ] Добавить конфигурацию в `config.ini`
- [ ] Создать `test_cave_world.py` - проверка генерации и особенностей мира
- [ ] Полнофункциональный мир-пещера готов для issue #02

#### 5.2 Подземный мир
- [ ] Создать `data/worlds/underground_world.txt` - мир с лавой и особыми врагами
- [ ] Создать `test_underground_world.py`
- [ ] Уникальная атмосфера и механики подземного мира

#### 5.3 Ледяной мир
- [ ] Создать `data/worlds/ice_world.txt` - заснеженный ландшафт с эффектом скольжения
- [ ] Создать `test_ice_world.py` - тестирование механик льда
- [ ] Эффект скольжения работает корректно

#### 5.4 Лесной мир
- [ ] Создать `data/worlds/forest_world.txt` - густой лес со скрытыми тропами
- [ ] Создать `test_forest_world.py`
- [ ] Визуально привлекательный лесной ландшафт

### 🔧 Фаза 6: Интеграция и оптимизация
**Цель**: Финальная интеграция и обеспечение производительности

#### 6.1 Интеграционные тесты
- [ ] Создать `tests/integration/test_multiworld_integration.py`
- [ ] Тестировать полный цикл: создание мира → телепортация → сохранение → загрузка
- [ ] Все интеграционные тесты проходят без ошибок

#### 6.2 Оптимизация производительности
- [ ] Профилирование производительности системы
- [ ] Создать `test_multiworld_performance.py` - тесты производительности
- [ ] Система работает стабильно на 60 FPS без утечек памяти

#### 6.3 Документация и конфигурация
- [ ] Обновить `config.ini` с настройками миров
- [ ] Обновить `CLAUDE.md` с документацией API
- [ ] Полная документация готова для других разработчиков

---

## 🌳 Дерево зависимостей подзадач

```
Фаза 1: Архитектурная подготовка
├── 1.1 Рефакторинг системы координат
├── 1.2 Создание базовых компонентов ECS (зависит от 1.1)
└── 1.3 Событийная система (зависит от 1.2)

Фаза 2: Фабричные паттерны
├── 2.1 Abstract Factory Pattern (зависит от 1.2, 1.3)
└── 2.2 Конкретные фабрики миров (зависит от 2.1)

Фаза 3: Система управления мирами
├── 3.1 WorldManager (зависит от 2.1, 2.2)
├── 3.2 PortalSystem (зависит от 3.1, 1.3)
└── 3.3 Система сохранения (зависит от 3.1, 3.2)

Фаза 4: UI и визуализация
├── 4.1 Экраны загрузки (зависит от 3.1)
├── 4.2 Визуальные эффекты (зависит от 3.2)
└── 4.3 UI выбора миров (зависит от 3.1, 4.1)

Фаза 5: Создание контента (может выполняться параллельно после завершения Фазы 3)
├── 5.1 Мир-пещера (зависит от 3.1, 2.2)
├── 5.2 Подземный мир (зависит от 3.1, 2.2)
├── 5.3 Ледяной мир (зависит от 3.1, 2.2)
└── 5.4 Лесной мир (зависит от 3.1, 2.2)

Фаза 6: Интеграция и оптимизация
├── 6.1 Интеграционные тесты (зависит от всех предыдущих фаз)
├── 6.2 Оптимизация производительности (зависит от 6.1)
└── 6.3 Документация (зависит от всех предыдущих фаз)
```

**Критический путь**: 1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 3.1 → 3.2 → 3.3 → 6.1 → 6.2 → 6.3

**Минимальные требования к тестированию**: 
- Unit тесты для каждого компонента и системы
- Интеграционные тесты для взаимодействия систем  
- Тесты производительности для предотвращения деградации
- Минимальное покрытие: 90% для критических компонентов