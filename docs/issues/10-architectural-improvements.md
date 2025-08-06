# Issue #10: Архитектурные улучшения

## Описание
Реализация архитектурных паттернов и улучшений для масштабируемости, производительности и поддерживаемости кода.

## Цель
Подготовить кодовую базу для масштабирования, улучшить производительность и упростить разработку новых функций.

## Требования

### Entity Component System (ECS)

#### Компонентная архитектура
- [ ] **Базовый компонент**:
  - [ ] Абстрактный класс Component
  - [ ] Система регистрации компонентов
  - [ ] Сериализация для сохранений
- [ ] **Игровые компоненты**:
  - [ ] HealthComponent: здоровье и урон
  - [ ] MagicComponent: мана и заклинания
  - [ ] SkillComponent: навыки и прогрессия
  - [ ] InventoryComponent: инвентарь и предметы
  - [ ] AIComponent: искусственный интеллект
  - [ ] RenderComponent: визуализация
  - [ ] PhysicsComponent: физика и коллизии

#### Система сущностей
- [ ] **Entity Manager**:
  - [ ] Создание и удаление сущностей
  - [ ] Управление компонентами
  - [ ] Поиск сущностей по компонентам
- [ ] **Типы сущностей**:
  - [ ] Player: игрок с полным набором компонентов
  - [ ] Enemy: враги с ИИ и боевыми компонентами
  - [ ] NPC: неигровые персонажи с диалогами
  - [ ] Item: предметы с характеристиками
  - [ ] Environmental: объекты окружения

#### Системы обработки
- [ ] **System Manager**:
  - [ ] Регистрация и управление системами
  - [ ] Порядок выполнения систем
  - [ ] Производительность и профилирование
- [ ] **Игровые системы**:
  - [ ] MovementSystem: обработка движения
  - [ ] CombatSystem: боевая система
  - [ ] RenderSystem: отрисовка
  - [ ] AISystem: искусственный интеллект
  - [ ] PhysicsSystem: физика и коллизии

### Паттерн Abstract Factory

#### Фабрики сущностей
- [ ] **EntityFactory (абстрактная)**:
  - [ ] Интерфейс для создания сущностей
  - [ ] Стандартизация процесса создания
  - [ ] Интеграция с ECS
- [ ] **Конкретные фабрики**:
  - [ ] PlayerFactory: создание игрока
  - [ ] EnemyFactory: создание врагов (10+ типов)
  - [ ] NPCFactory: создание NPC
  - [ ] ItemFactory: создание предметов
  - [ ] EnvironmentFactory: объекты окружения

#### Система конфигурации фабрик
- [ ] **JSON конфигурации**:
  - [ ] Описание шаблонов сущностей
  - [ ] Параметры компонентов
  - [ ] Вариации и случайная генерация
- [ ] **Загрузка конфигураций**:
  - [ ] Парсинг JSON файлов
  - [ ] Валидация параметров
  - [ ] Горячая перезагрузка (для разработки)

### Паттерн Observer

#### Система событий
- [ ] **Event Manager**:
  - [ ] Регистрация слушателей событий
  - [ ] Отправка событий
  - [ ] Приоритеты обработки
- [ ] **Типы событий**:
  - [ ] PlayerEvents: смерть, повышение уровня, получение предмета
  - [ ] CombatEvents: атака, блокировка, критический удар
  - [ ] QuestEvents: получение, выполнение, завершение квеста
  - [ ] WorldEvents: смена мира, активация портала
- [ ] **Интеграция с системами**:
  - [ ] Статистика реагирует на события
  - [ ] Квесты отслеживают прогресс
  - [ ] UI обновляется при изменениях

### Паттерн State Machine

#### Система состояний игры
- [ ] **GameStateManager**:
  - [ ] Управление состояниями игры
  - [ ] Переходы между состояниями
  - [ ] Стек состояний для вложенности
- [ ] **Состояния игры**:
  - [ ] MenuState: главное меню
  - [ ] PlayingState: основная игра
  - [ ] PausedState: пауза
  - [ ] InventoryState: инвентарь
  - [ ] DialogState: диалоги с NPC
  - [ ] GameOverState: экран смерти

#### Состояния ИИ
- [ ] **AI State Machine**:
  - [ ] Состояния поведения врагов
  - [ ] Переходы между состояниями
  - [ ] Условия активации
- [ ] **Состояния врагов**:
  - [ ] IdleState: покой
  - [ ] PatrolState: патрулирование
  - [ ] ChaseState: преследование
  - [ ] AttackState: атака
  - [ ] FleeState: бегство

### Система ресурсов

#### Resource Manager
- [ ] **Управление ресурсами**:
  - [ ] Загрузка и кэширование ресурсов
  - [ ] Автоматическое освобождение памяти
  - [ ] Асинхронная загрузка
- [ ] **Типы ресурсов**:
  - [ ] Текстуры и спрайты
  - [ ] Звуковые эффекты
  - [ ] Конфигурационные файлы
  - [ ] Карты и уровни
- [ ] **Оптимизация**:
  - [ ] Предзагрузка критических ресурсов
  - [ ] Выгрузка неиспользуемых ресурсов
  - [ ] Сжатие и оптимизация размера

### Система логирования

#### Logger System
- [ ] **Уровни логирования**:
  - [ ] DEBUG: отладочная информация
  - [ ] INFO: общая информация
  - [ ] WARNING: предупреждения
  - [ ] ERROR: ошибки
  - [ ] CRITICAL: критические ошибки
- [ ] **Вывод логов**:
  - [ ] Консоль для разработки
  - [ ] Файлы для продакшена
  - [ ] Фильтрация по категориям
- [ ] **Интеграция**:
  - [ ] Логирование всех важных событий
  - [ ] Отслеживание производительности
  - [ ] Диагностика ошибок

## Технические детали

### Файлы для создания/изменения
- `src/ecs/component.py` - базовые компоненты
- `src/ecs/entity.py` - система сущностей
- `src/ecs/system.py` - системы обработки
- `src/factories/entity_factory.py` - фабрики сущностей
- `src/events/event_manager.py` - система событий
- `src/states/state_manager.py` - управление состояниями
- `src/resources/resource_manager.py` - управление ресурсами
- `src/utils/logger.py` - система логирования

### Архитектура ECS
```python
class Component:
    """Базовый компонент для ECS"""
    def __init__(self):
        self.entity_id = None
        
class Entity:
    """Игровая сущность"""
    def __init__(self, entity_id):
        self.id = entity_id
        self.components = {}
        
    def add_component(self, component):
        self.components[type(component)] = component
        component.entity_id = self.id
        
    def get_component(self, component_type):
        return self.components.get(component_type)

class System:
    """Базовая система обработки"""
    def __init__(self):
        self.required_components = []
        
    def update(self, dt, entities):
        for entity in entities:
            if self.has_required_components(entity):
                self.process_entity(entity, dt)
```

### Конфигурация
```ini
[ARCHITECTURE]
enable_ecs = true
enable_logging = true
log_level = INFO
resource_cache_size = 100

[PERFORMANCE]
max_entities = 1000
system_profiling = true
memory_monitoring = true
target_fps = 60

[FACTORIES]
config_path = data/entities/
auto_reload_configs = false
validation_enabled = true
```

### Интеграция всех архитектурных паттернов

#### Центральная архитектура проекта
```python
# src/core/game_architecture.py
class GameArchitecture:
    """Центральный класс архитектуры игры"""
    def __init__(self):
        # Основные системы
        self.entity_manager = EntityManager()
        self.component_manager = ComponentManager()
        self.system_manager = SystemManager()
        self.event_system = EventSystem()
        self.resource_manager = ResourceManager()
        
        # Фабрики
        self.entity_factories = {
            'world': WorldFactory(),
            'enemy': EnemyFactory(),
            'item': ItemFactory(),
            'quest': QuestFactory()
        }
        
        # Инициализация всех систем
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Инициализация всех ECS систем в правильном порядке"""
        # Базовые системы
        self.system_manager.add_system(PhysicsSystem(self.event_system))
        self.system_manager.add_system(MovementSystem())
        
        # Игровые системы
        self.system_manager.add_system(MagicSystem(self.event_system))
        self.system_manager.add_system(CombatSystem(self.event_system))
        self.system_manager.add_system(AISystem(self.event_system))
        
        # Системы прогрессии
        self.system_manager.add_system(ProgressionSystem(self.event_system))
        self.system_manager.add_system(QuestTracker(self.event_system))
        
        # Системы мира
        self.system_manager.add_system(WorldSystem(self.event_system))
        self.system_manager.add_system(EventBoxSystem(self.event_system))
        
        # UI системы
        self.system_manager.add_system(RenderSystem())
        self.system_manager.add_system(UISystem())
```

#### Dependency Injection Container
```python
# src/core/dependency_injection.py
class DIContainer:
    """Контейнер для Dependency Injection"""
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register_singleton(self, interface: type, implementation: type):
        """Регистрация синглтона"""
        self._services[interface] = ('singleton', implementation)
    
    def register_transient(self, interface: type, implementation: type):
        """Регистрация временного объекта"""
        self._services[interface] = ('transient', implementation)
    
    def resolve(self, interface: type):
        """Получение экземпляра сервиса"""
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        
        service_type, implementation = self._services[interface]
        
        if service_type == 'singleton':
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(implementation)
            return self._singletons[interface]
        else:
            return self._create_instance(implementation)
    
    def _create_instance(self, implementation: type):
        """Создание экземпляра с автоматическим разрешением зависимостей"""
        # Автоматическое внедрение зависимостей через конструктор
        import inspect
        signature = inspect.signature(implementation.__init__)
        dependencies = {}
        
        for param_name, param in signature.parameters.items():
            if param_name != 'self' and param.annotation != inspect.Parameter.empty:
                dependencies[param_name] = self.resolve(param.annotation)
        
        return implementation(**dependencies)

# Настройка DI контейнера
def setup_dependency_injection() -> DIContainer:
    container = DIContainer()
    
    # Регистрация основных сервисов
    container.register_singleton(EventSystem, EventSystem)
    container.register_singleton(ResourceManager, ResourceManager)
    container.register_singleton(EntityManager, EntityManager)
    
    # Регистрация фабрик
    container.register_singleton(WorldFactory, StandardWorldFactory)
    container.register_singleton(EnemyFactory, StandardEnemyFactory)
    container.register_singleton(ItemFactory, StandardItemFactory)
    
    # Регистрация систем
    container.register_singleton(MagicSystem, MagicSystem)
    container.register_singleton(CombatSystem, CombatSystem)
    container.register_singleton(QuestTracker, QuestTracker)
    
    return container
```

#### Конфигурационная система
```python
# src/core/configuration.py
class ConfigurationManager:
    """Управление конфигурацией с паттерном Singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_data = {}
            self.config_files = [
                'config/game.ini',
                'config/balance.ini',
                'config/graphics.ini'
            ]
            self._load_all_configs()
            self._initialized = True
    
    def get(self, section: str, key: str, default=None):
        """Получение значения конфигурации"""
        return self.config_data.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value):
        """Установка значения конфигурации"""
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
```

### Миграция существующего кода

#### Поэтапный план миграции
```python
# Этап 1: Создание базовой ECS инфраструктуры
class MigrationStep1:
    """Создание ECS компонентов для существующих классов"""
    def migrate_player(self, old_player: Player) -> Entity:
        entity = Entity()
        
        # Миграция данных в компоненты
        entity.add_component(PositionComponent(old_player.x, old_player.y))
        entity.add_component(HealthComponent(old_player.max_hp))
        entity.add_component(RenderComponent(old_player.sprite))
        
        # Добавление новых компонентов
        entity.add_component(MagicComponent(100))  # новая функциональность
        entity.add_component(InventoryComponent(10, 6))
        
        return entity

# Этап 2: Миграция систем
class MigrationStep2:
    """Замена монолитных классов на ECS системы"""
    def migrate_combat_system(self, old_combat_logic):
        # Создание новой системы боя с паттернами
        combat_system = CombatSystem(self.event_system)
        
        # Миграция стратегий
        combat_system.add_strategy("melee", MeleeWeaponStrategy())
        combat_system.add_strategy("ranged", RangedWeaponStrategy())
        combat_system.add_strategy("magic", MagicWeaponStrategy())
        
        return combat_system

# Этап 3: Интеграция событийной системы
class MigrationStep3:
    """Замена прямых вызовов на события"""
    def migrate_to_events(self):
        # Старый код: direct call
        # player.take_damage(damage)
        
        # Новый код: через события
        self.event_system.emit(DamageEvent(player, damage, source))
```

#### Обратная совместимость
```python
# src/core/compatibility.py
class CompatibilityLayer:
    """Слой обратной совместимости для старого API"""
    def __init__(self, game_architecture: GameArchitecture):
        self.architecture = game_architecture
    
    def get_player_old_style(self) -> 'PlayerWrapper':
        """Возвращает обертку над ECS сущностью в старом стиле"""
        player_entity = self.architecture.get_player_entity()
        return PlayerWrapper(player_entity)

class PlayerWrapper:
    """Обертка для обратной совместимости"""
    def __init__(self, entity: Entity):
        self._entity = entity
    
    @property
    def x(self) -> float:
        return self._entity.get_component(PositionComponent).x
    
    @x.setter
    def x(self, value: float):
        self._entity.get_component(PositionComponent).x = value
    
    def take_damage(self, damage: int):
        # Преобразование в новый API
        health_comp = self._entity.get_component(HealthComponent)
        health_comp.current_hp -= damage
```

### Тестирование архитектуры

#### Юнит-тесты компонентов
```python
# tests/test_ecs_components.py
class TestECSComponents:
    def test_health_component(self):
        health = HealthComponent(100)
        assert health.max_hp == 100
        assert health.current_hp == 100
        
        health.take_damage(30)
        assert health.current_hp == 70
        assert not health.is_dead()
        
        health.take_damage(80)
        assert health.is_dead()
    
    def test_magic_component(self):
        magic = MagicComponent(50)
        assert magic.max_mana == 50
        
        magic.cast_spell(20)
        assert magic.current_mana == 30
```

#### Интеграционные тесты систем
```python
# tests/test_system_integration.py
class TestSystemIntegration:
    def test_combat_magic_integration(self):
        # Создание тестовых сущностей
        player = self.create_test_player()
        enemy = self.create_test_enemy()
        
        # Тест магической атаки
        magic_system = MagicSystem(self.event_system)
        combat_system = CombatSystem(self.event_system)
        
        # Применение заклинания
        spell = FireBoltSpell()
        magic_system.cast_spell(player, spell, enemy.position)
        
        # Проверка результата
        enemy_health = enemy.get_component(HealthComponent)
        assert enemy_health.current_hp < enemy_health.max_hp
```

#### Тесты производительности
```python
# tests/test_performance.py
class TestPerformance:
    def test_ecs_performance_1000_entities(self):
        """Тест производительности с 1000 сущностей"""
        start_time = time.time()
        
        # Создание 1000 сущностей
        entities = []
        for i in range(1000):
            entity = Entity()
            entity.add_component(PositionComponent(i, i))
            entity.add_component(HealthComponent(100))
            entities.append(entity)
        
        # Обновление всех систем
        for _ in range(60):  # 60 FPS
            self.system_manager.update(16.67)  # ~16.67ms per frame
        
        end_time = time.time()
        assert (end_time - start_time) < 1.0  # Должно выполниться за секунду
```

## Критерии готовности
- [ ] ECS система полностью функциональна
- [ ] Фабрики создают все типы сущностей
- [ ] Система событий работает корректно
- [ ] State Machine управляет состояниями
- [ ] Resource Manager оптимизирует память
- [ ] Логирование покрывает все важные события
- [ ] Производительность не ухудшилась
- [ ] Код стал более модульным и тестируемым

## Приоритет
**Средний** - Важно для долгосрочного развития

## Зависимости
- Все существующие системы (для миграции)
- Система тестирования
- Инструменты профилирования

## Преимущества внедрения
- **Масштабируемость**: легко добавлять новые типы сущностей
- **Производительность**: оптимизированная обработка компонентов
- **Тестируемость**: изолированные компоненты и системы
- **Поддерживаемость**: четкое разделение ответственности
- **Гибкость**: легкое комбинирование компонентов

## Риски и сложности
- **Сложность миграции**: требует переработки существующего кода
- **Кривая обучения**: команда должна изучить новые паттерны
- **Производительность**: неправильная реализация может замедлить игру
- **Время разработки**: значительные временные затраты

## Примерное время реализации
6-8 недель (включая миграцию)

## Связанные issues
- Все предыдущие issues (для интеграции с новой архитектурой)
- Система тестирования
- Документация архитектуры