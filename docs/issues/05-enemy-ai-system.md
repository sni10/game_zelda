# Issue #05: Система ИИ врагов

## Описание
Реализация интеллектуальной системы врагов с различными типами поведения, патрулированием и тактическими способностями.

## Цель
Создать разнообразных врагов с уникальным поведением для повышения сложности и интереса к боевой системе.

## Требования

### Типы врагов

#### Ходячие враги
- [ ] **Стрелок**:
  - [ ] Размер: 32x32, красный цвет
  - [ ] Поведение: патрулирование по заданному маршруту
  - [ ] Атака: дальняя стрельба стрелами
  - [ ] ИИ: обнаружение игрока, преследование на расстоянии
  - [ ] Дроп: стрелы, опыт, иногда лук
- [ ] **Мечник**:
  - [ ] Размер: 32x32, темно-красный цвет
  - [ ] Поведение: патрулирование, агрессивное преследование
  - [ ] Атака: ближняя рукопашная
  - [ ] ИИ: прямое преследование, атака в упор
  - [ ] Дроп: оружие ближнего боя, опыт

#### Быстрые враги
- [ ] **Бегающий боец**:
  - [ ] Размер: 28x28, оранжевый цвет
  - [ ] Поведение: быстрое перемещение, уклонение
  - [ ] Тактика: подбег → серия ударов → отбег
  - [ ] ИИ: хитрое позиционирование, избегание атак
  - [ ] Дроп: зелья скорости, опыт

#### Магические враги (расширение)
- [ ] **Элементальный маг**:
  - [ ] Использует одну из трех стихий
  - [ ] Дальние магические атаки
  - [ ] Телепортация при опасности
  - [ ] Дроп: магические предметы, руны

### Система ИИ

#### Состояния поведения
- [ ] **PATROL** - патрулирование:
  - [ ] Движение по заданному маршруту
  - [ ] Поиск игрока в радиусе обнаружения
  - [ ] Возврат к патрулированию при потере цели
- [ ] **ALERT** - обнаружение:
  - [ ] Переход к преследованию
  - [ ] Увеличенная скорость движения
  - [ ] Вызов подкрепления (групповое поведение)
- [ ] **COMBAT** - бой:
  - [ ] Активные атаки по игроку
  - [ ] Использование тактических способностей
  - [ ] Попытки окружения (для групп)
- [ ] **RETREAT** - отступление:
  - [ ] При низком здоровье
  - [ ] Поиск укрытия или союзников
  - [ ] Использование лечебных предметов

#### Параметры ИИ
- [ ] **Радиус обнаружения**: 100-150 пикселей
- [ ] **Радиус атаки**: зависит от типа врага
- [ ] **Скорость патрулирования**: 60 пикс/сек
- [ ] **Скорость преследования**: 100 пикс/сек
- [ ] **Время памяти**: 5 секунд после потери игрока

### Групповое поведение
- [ ] **Координация атак**:
  - [ ] Враги атакуют с разных сторон
  - [ ] Стрелки прикрывают мечников
  - [ ] Быстрые враги отвлекают внимание
- [ ] **Система сигналов**:
  - [ ] Враги предупреждают друг друга об опасности
  - [ ] Радиус распространения сигнала
  - [ ] Визуальные индикаторы тревоги

## Технические детали

### Архитектурные паттерны

#### ECS Components для системы ИИ
```python
# src/core/ecs/ai_components.py
class AIComponent(Component):
    """Компонент искусственного интеллекта"""
    def __init__(self, ai_type: str):
        self.ai_type = ai_type  # ARCHER, WARRIOR, RUNNER, MAGE
        self.current_state = None
        self.target = None
        self.detection_radius = 120
        self.attack_radius = 40
        self.memory_time = 5000  # мс
        self.last_seen_player_pos = None
        self.last_seen_time = 0

class PatrolComponent(Component):
    """Компонент патрулирования"""
    def __init__(self, patrol_points: List[tuple]):
        self.patrol_points = patrol_points
        self.current_point_index = 0
        self.patrol_speed = 60
        self.wait_time_at_point = 2000  # мс
        self.current_wait_time = 0

class GroupBehaviorComponent(Component):
    """Компонент группового поведения"""
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.group_members = []
        self.is_group_leader = False
        self.communication_radius = 150
        self.last_alert_time = 0

class CombatAIComponent(Component):
    """Компонент боевого ИИ"""
    def __init__(self):
        self.preferred_distance = 0  # 0 для ближнего боя, >0 для дальнего
        self.retreat_health_threshold = 0.3  # отступать при 30% здоровья
        self.aggression_level = 1.0  # множитель агрессивности
        self.combat_tactics = []
```

#### State Pattern для поведения ИИ
```python
# src/ai/behavior_states.py
class AIState(ABC):
    """Базовое состояние ИИ"""
    
    @abstractmethod
    def enter(self, entity: Entity):
        pass
    
    @abstractmethod
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        pass
    
    @abstractmethod
    def exit(self, entity: Entity):
        pass

class IdleState(AIState):
    """Состояние покоя"""
    def enter(self, entity: Entity):
        # Сброс целей и остановка движения
        ai_comp = entity.get_component(AIComponent)
        ai_comp.target = None
    
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        ai_comp = entity.get_component(AIComponent)
        
        # Поиск игрока в радиусе обнаружения
        player = world.get_player()
        if self._can_see_player(entity, player):
            ai_comp.target = player
            return AlertState()
        
        # Переход к патрулированию если есть маршрут
        patrol_comp = entity.get_component(PatrolComponent)
        if patrol_comp and patrol_comp.patrol_points:
            return PatrolState()
        
        return None

class PatrolState(AIState):
    """Состояние патрулирования"""
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        ai_comp = entity.get_component(AIComponent)
        patrol_comp = entity.get_component(PatrolComponent)
        
        # Проверка на обнаружение игрока
        player = world.get_player()
        if self._can_see_player(entity, player):
            ai_comp.target = player
            self._alert_group_members(entity, world)
            return AlertState()
        
        # Движение по маршруту патрулирования
        self._move_to_next_patrol_point(entity, dt)
        return None

class AlertState(AIState):
    """Состояние тревоги"""
    def enter(self, entity: Entity):
        ai_comp = entity.get_component(AIComponent)
        ai_comp.last_seen_time = pygame.time.get_ticks()
    
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        ai_comp = entity.get_component(AIComponent)
        
        if ai_comp.target:
            # Переход к преследованию
            return ChaseState()
        
        # Потеря цели - возврат к патрулированию
        current_time = pygame.time.get_ticks()
        if current_time - ai_comp.last_seen_time > ai_comp.memory_time:
            return PatrolState()
        
        return None

class ChaseState(AIState):
    """Состояние преследования"""
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        ai_comp = entity.get_component(AIComponent)
        combat_comp = entity.get_component(CombatAIComponent)
        
        if not ai_comp.target:
            return AlertState()
        
        distance_to_target = self._get_distance(entity, ai_comp.target)
        
        # Переход к бою если цель в радиусе атаки
        if distance_to_target <= ai_comp.attack_radius:
            return CombatState()
        
        # Движение к цели
        self._move_towards_target(entity, ai_comp.target, dt)
        
        # Проверка на отступление
        health_comp = entity.get_component(HealthComponent)
        if (health_comp.current_hp / health_comp.max_hp) < combat_comp.retreat_health_threshold:
            return RetreatState()
        
        return None

class CombatState(AIState):
    """Состояние боя"""
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        ai_comp = entity.get_component(AIComponent)
        combat_comp = entity.get_component(CombatAIComponent)
        
        if not ai_comp.target:
            return AlertState()
        
        # Выполнение боевой тактики в зависимости от типа врага
        self._execute_combat_behavior(entity, ai_comp.target, dt)
        
        # Проверка на отступление
        health_comp = entity.get_component(HealthComponent)
        if (health_comp.current_hp / health_comp.max_hp) < combat_comp.retreat_health_threshold:
            return RetreatState()
        
        # Если цель далеко - преследовать
        distance = self._get_distance(entity, ai_comp.target)
        if distance > ai_comp.attack_radius * 1.5:
            return ChaseState()
        
        return None

class RetreatState(AIState):
    """Состояние отступления"""
    def update(self, entity: Entity, world: World, dt: float) -> Optional[AIState]:
        # Поиск укрытия или союзников
        safe_position = self._find_safe_position(entity, world)
        self._move_towards_position(entity, safe_position, dt)
        
        # Возврат к бою если здоровье восстановилось
        health_comp = entity.get_component(HealthComponent)
        if health_comp.current_hp / health_comp.max_hp > 0.7:
            return ChaseState()
        
        return None
```

#### Strategy Pattern для различных типов врагов
```python
# src/ai/enemy_strategies.py
class EnemyBehaviorStrategy(ABC):
    """Стратегия поведения врага"""
    
    @abstractmethod
    def execute_combat(self, entity: Entity, target: Entity, dt: float):
        pass
    
    @abstractmethod
    def get_preferred_distance(self) -> float:
        pass

class ArcherStrategy(EnemyBehaviorStrategy):
    """Стратегия лучника"""
    def execute_combat(self, entity: Entity, target: Entity, dt: float):
        # Поддержание дистанции и стрельба
        distance = self._get_distance(entity, target)
        preferred_distance = self.get_preferred_distance()
        
        if distance < preferred_distance:
            # Отступить на безопасную дистанцию
            self._move_away_from_target(entity, target, dt)
        elif distance > preferred_distance * 1.5:
            # Приблизиться для точной стрельбы
            self._move_towards_target(entity, target, dt)
        else:
            # Стрелять
            self._shoot_at_target(entity, target)
    
    def get_preferred_distance(self) -> float:
        return 100  # пикселей

class WarriorStrategy(EnemyBehaviorStrategy):
    """Стратегия воина"""
    def execute_combat(self, entity: Entity, target: Entity, dt: float):
        # Агрессивное приближение и атака
        distance = self._get_distance(entity, target)
        
        if distance > 32:  # дальность меча
            self._move_towards_target(entity, target, dt)
        else:
            self._melee_attack(entity, target)
    
    def get_preferred_distance(self) -> float:
        return 32  # ближний бой

class RunnerStrategy(EnemyBehaviorStrategy):
    """Стратегия быстрого врага"""
    def execute_combat(self, entity: Entity, target: Entity, dt: float):
        # Тактика "подбег-удар-отбег"
        combat_comp = entity.get_component(CombatAIComponent)
        
        if not hasattr(combat_comp, 'attack_phase'):
            combat_comp.attack_phase = 'approach'
            combat_comp.phase_timer = 0
        
        combat_comp.phase_timer += dt
        
        if combat_comp.attack_phase == 'approach':
            self._move_towards_target(entity, target, dt * 1.5)  # быстрое движение
            if self._get_distance(entity, target) < 40:
                combat_comp.attack_phase = 'attack'
                combat_comp.phase_timer = 0
        
        elif combat_comp.attack_phase == 'attack':
            self._melee_attack(entity, target)
            if combat_comp.phase_timer > 500:  # 0.5 секунды атаки
                combat_comp.attack_phase = 'retreat'
                combat_comp.phase_timer = 0
        
        elif combat_comp.attack_phase == 'retreat':
            self._move_away_from_target(entity, target, dt * 1.2)
            if combat_comp.phase_timer > 1000:  # 1 секунда отступления
                combat_comp.attack_phase = 'approach'
                combat_comp.phase_timer = 0
```

#### Observer Pattern для группового поведения
```python
# src/ai/group_behavior.py
class GroupBehaviorSystem(System):
    """Система группового поведения"""
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        self.groups = {}  # group_id -> [entities]
        
        # Подписка на события
        self.event_system.subscribe("enemy_alerted", self.handle_enemy_alert)
        self.event_system.subscribe("enemy_died", self.handle_enemy_death)
    
    def handle_enemy_alert(self, event: EnemyAlertEvent):
        """Обработка тревоги врага"""
        alerting_entity = event.entity
        group_comp = alerting_entity.get_component(GroupBehaviorComponent)
        
        if group_comp:
            # Оповещение всех членов группы
            for member in group_comp.group_members:
                if member != alerting_entity:
                    self._alert_group_member(member, event.player_position)
    
    def _alert_group_member(self, entity: Entity, player_pos: tuple):
        """Оповещение члена группы"""
        ai_comp = entity.get_component(AIComponent)
        group_comp = entity.get_component(GroupBehaviorComponent)
        
        # Проверка дистанции для коммуникации
        distance = self._get_distance_to_position(entity, player_pos)
        if distance <= group_comp.communication_radius:
            ai_comp.last_seen_player_pos = player_pos
            ai_comp.last_seen_time = pygame.time.get_ticks()
            
            # Переход в состояние тревоги
            ai_comp.current_state = AlertState()

class CoordinatedAttackStrategy:
    """Стратегия координированной атаки"""
    def __init__(self, group_members: List[Entity]):
        self.group_members = group_members
        self.formation_positions = self._calculate_formation()
    
    def execute_coordinated_attack(self, target: Entity):
        """Выполнение координированной атаки"""
        for i, member in enumerate(self.group_members):
            formation_pos = self.formation_positions[i]
            target_pos = self._calculate_attack_position(target, formation_pos)
            
            # Каждый член группы движется к своей позиции
            self._move_to_formation_position(member, target_pos)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── ai_components.py          # Компоненты ИИ
├── ai/
│   ├── behavior_states.py        # Состояния поведения (State Pattern)
│   ├── enemy_strategies.py       # Стратегии врагов (Strategy Pattern)
│   ├── group_behavior.py         # Групповое поведение (Observer Pattern)
│   ├── pathfinding.py            # Поиск пути
│   ├── ai_system.py              # Основная система ИИ (ECS System)
│   └── state_machine.py          # Машина состояний
├── entities/
│   ├── enemy_factory.py          # Фабрика врагов (Abstract Factory)
│   └── enemy_types.py            # Различные типы врагов
└── events/
    └── ai_events.py              # События ИИ
```

### Файлы для создания/изменения
- `src/core/ecs/ai_components.py` - компоненты ИИ
- `src/ai/behavior_states.py` - состояния поведения (State Pattern)
- `src/ai/enemy_strategies.py` - стратегии врагов (Strategy Pattern)
- `src/ai/group_behavior.py` - групповое поведение (Observer Pattern)
- `src/ai/ai_system.py` - основная система ИИ (ECS System)
- `src/ai/state_machine.py` - машина состояний
- `src/entities/enemy_factory.py` - фабрика врагов
- `src/events/ai_events.py` - события ИИ
- `src/ai/pathfinding.py` - поиск пути

### Архитектура ИИ
```python
class EnemyAI:
    def __init__(self, enemy, detection_radius, attack_radius):
        self.enemy = enemy
        self.state = AIState.PATROL
        self.target = None
        self.patrol_points = []
        self.detection_radius = detection_radius
        
    def update(self, dt, player_pos):
        if self.state == AIState.PATROL:
            self.patrol_behavior(dt)
        elif self.state == AIState.COMBAT:
            self.combat_behavior(dt, player_pos)
```

### Система патрулирования
- [ ] **Маршруты патрулирования**:
  - [ ] Линейные маршруты (туда-обратно)
  - [ ] Круговые маршруты
  - [ ] Случайное блуждание в области
- [ ] **Точки интереса**:
  - [ ] Стационарные позиции (охрана)
  - [ ] Ключевые локации для защиты
  - [ ] Переходы между областями

### Конфигурация
```ini
[ENEMY_AI]
detection_radius = 120
attack_radius = 40
patrol_speed = 60
chase_speed = 100
memory_time = 5000

[ENEMY_TYPES]
archer_health = 50
archer_damage = 15
warrior_health = 80
warrior_damage = 25
runner_health = 30
runner_damage = 20
runner_speed = 140
```

## Критерии готовности
- [ ] Минимум 3 типа врагов с уникальным поведением
- [ ] ИИ корректно переключается между состояниями
- [ ] Патрулирование работает без зависаний
- [ ] Групповое поведение координируется
- [ ] Враги не застревают в препятствиях
- [ ] Производительность остается стабильной при 10+ врагах

## Приоритет
**Высокий** - Критически важно для игрового процесса

## Зависимости
- Текущая система врагов (Enemy)
- Issue #04 (Оружие) - для дропа предметов
- Система коллизий и навигации

## Балансировка
- Стрелки должны держать дистанцию
- Мечники должны быть опасны в ближнем бою
- Быстрые враги должны быть уязвимы при правильной тактике
- Групповые атаки не должны быть непобедимыми

## Расширения (низкий приоритет)
- [ ] **Элитные враги**: уникальные способности
- [ ] **Боссы**: сложные паттерны атак
- [ ] **Адаптивный ИИ**: изучение тактики игрока
- [ ] **Эмоциональные реакции**: страх, ярость, паника

## Примерное время реализации
4-5 недель

## Связанные issues
- #04 (Оружие) - дроп предметов
- #07 (Event boxes) - спаун врагов
- #08 (Инвентарь) - система дропа
- #09 (Квесты) - враги как цели квестов

---

## Подзадачи для реализации

### 🧠 Фаза 1: Базовая архитектура ИИ
**Цель**: Создание ECS компонентов и базовой архитектуры для ИИ

#### 1.1 ECS компоненты ИИ
- [ ] Создать `src/core/ecs/ai_components.py` - AIComponent, PatrolComponent, GroupBehaviorComponent
- [ ] Создать CombatAIComponent для боевого поведения
- [ ] Создать `test_ai_components.py` - unit тесты всех компонентов ИИ
- [ ] Все компоненты ИИ работают корректно с базовой функциональностью

#### 1.2 Система событий ИИ
- [ ] Создать `src/events/ai_events.py` - EnemyAlertEvent, EnemyAttackEvent, EnemyDeathEvent
- [ ] Создать GroupCommunicationEvent для группового поведения
- [ ] Создать `test_ai_events.py` - тестирование событий ИИ
- [ ] События ИИ корректно обрабатываются системой

#### 1.3 Базовая система ИИ как ECS System
- [ ] Создать `src/ai/ai_system.py` - центральная AISystem (ECS System)
- [ ] Интеграция с системой событий
- [ ] Создать `test_ai_system.py` - тестирование базовой системы ИИ
- [ ] Система ИИ корректно обрабатывает сущности с компонентами ИИ

### 🤖 Фаза 2: State Pattern для поведения врагов
**Цель**: Реализация машины состояний для различных типов поведения

#### 2.1 Базовые состояния поведения
- [ ] Создать `src/ai/behavior_states.py` - AIState, IdleState, PatrolState
- [ ] Создать AlertState, ChaseState, CombatState, RetreatState
- [ ] Создать `test_behavior_states.py` - тестирование всех состояний
- [ ] Все состояния корректно переключаются друг в друга

#### 2.2 Машина состояний
- [ ] Создать `src/ai/state_machine.py` - StateMachine для управления переходами
- [ ] Система приоритетов и условий переходов
- [ ] Создать `test_state_machine.py` - тестирование машины состояний
- [ ] Машина состояний корректно управляет поведением врагов

#### 2.3 Интеграция состояний с ИИ
- [ ] Обновить AISystem для работы с машиной состояний
- [ ] Создать StateTransitionSystem (ECS System)
- [ ] Создать `test_ai_state_integration.py` - тестирование интеграции состояний
- [ ] Враги корректно переключаются между состояниями

### 📊 Фаза 3: Strategy Pattern для типов врагов
**Цель**: Различные стратегии поведения для разных типов врагов

#### 3.1 Базовые стратегии врагов
- [ ] Создать `src/ai/enemy_strategies.py` - EnemyBehaviorStrategy, ArcherStrategy
- [ ] Создать WarriorStrategy, RunnerStrategy
- [ ] Создать `test_enemy_strategies.py` - тестирование стратегий врагов
- [ ] Каждая стратегия имеет уникальное боевое поведение

#### 3.2 Расширенные стратегии
- [ ] Создать MageStrategy для магических врагов (расширение)
- [ ] Создать BossStrategy для особых врагов
- [ ] Создать `test_advanced_strategies.py` - тестирование расширенных стратегий
- [ ] Сложные враги имеют сложное тактическое поведение

#### 3.3 Интеграция стратегий с состояниями
- [ ] Связать стратегии с состояниями для контекстного поведения
- [ ] Создать StrategyManager для динамической смены стратегий
- [ ] Создать `test_strategy_state_integration.py` - тестирование интеграции
- [ ] Стратегии корректно работают в разных состояниях

### 🗺️ Фаза 4: Система патрулирования и навигации
**Цель**: Перемещение врагов и поиск пути

#### 4.1 Система патрулирования
- [ ] Создать PatrolSystem (ECS System) для управления маршрутами
- [ ] Поддержка линейных, круговых маршрутов и случайного блуждания
- [ ] Создать `test_patrol_system.py` - тестирование патрулирования
- [ ] Враги корректно патрулируют по заданным маршрутам

#### 4.2 Базовый поиск пути
- [ ] Создать `src/ai/pathfinding.py` - простейший pathfinding для обхода препятствий
- [ ] Интеграция с системой коллизий
- [ ] Создать `test_pathfinding.py` - тестирование поиска пути
- [ ] Враги не застревают в препятствиях при движении к цели

#### 4.3 Система преследования
- [ ] Создать ChaseSystem (ECS System) для умного преследования игрока
- [ ] Предсказание пути игрока и перехват
- [ ] Создать `test_chase_system.py` - тестирование преследования
- [ ] Враги эффективно преследуют игрока

### 👥 Фаза 5: Групповое поведение
**Цель**: Observer Pattern для координации нескольких врагов

#### 5.1 Система групповой коммуникации
- [ ] Создать `src/ai/group_behavior.py` - GroupBehaviorSystem (ECS System + Observer)
- [ ] Система сигналов тревоги между врагами
- [ ] Создать `test_group_behavior.py` - тестирование группового поведения
- [ ] Враги предупреждают друг друга об опасности

#### 5.2 Координированные атаки
- [ ] Создать CoordinatedAttackStrategy для групповых атак
- [ ] Система формаций и окружения игрока
- [ ] Создать `test_coordinated_attacks.py` - тестирование координированных атак
- [ ] Группы врагов атакуют координированно

#### 5.3 Групповые тактики
- [ ] Создать различные тактики: "танк+лучник", "окружение", "отвлечение"
- [ ] Система ролей в группе (лидер, поддержка, атака)
- [ ] Создать `test_group_tactics.py` - тестирование групповых тактик
- [ ] Группы врагов используют тактическое преимущество

### 🎯 Фаза 6: Интеграция и оптимизация
**Цель**: Финальная интеграция и обеспечение производительности

#### 6.1 Интеграция с боевой системой
- [ ] Связать ИИ с системой атаки и получения урона
- [ ] Обновить систему атаки игрока для работы с ИИ врагов
- [ ] Создать `test_ai_combat_integration.py` - интеграционные тесты боевой системы
- [ ] ИИ корректно реагирует на атаки и наносит ответный урон

#### 6.2 Фабрика врагов с ИИ
- [ ] Обновить `src/entities/enemy_factory.py` - интеграция с ИИ компонентами
- [ ] Создание врагов с предустановленными стратегиями и состояниями
- [ ] Создать `test_enemy_factory_ai.py` - тестирование фабрики врагов с ИИ
- [ ] Различные типы врагов создаются с соответствующим ИИ

#### 6.3 Оптимизация производительности
- [ ] Профилирование системы ИИ при большом количестве врагов
- [ ] Оптимизация расчетов состояний и поиска пути
- [ ] Создать `test_ai_performance.py` - тесты производительности ИИ
- [ ] Система ИИ работает стабильно с 10+ врагами одновременно

---

## 🌳 Дерево зависимостей подзадач

```
Фаза 1: Базовая архитектура ИИ
├── 1.1 ECS компоненты ИИ
├── 1.2 Система событий ИИ (зависит от 1.1)
└── 1.3 Базовая система ИИ (зависит от 1.1, 1.2)

Фаза 2: State Pattern для поведения
├── 2.1 Базовые состояния (зависит от 1.1)
├── 2.2 Машина состояний (зависит от 2.1)
└── 2.3 Интеграция состояний (зависит от 2.2, 1.3)

Фаза 3: Strategy Pattern для типов врагов
├── 3.1 Базовые стратегии (зависит от 2.1)
├── 3.2 Расширенные стратегии (зависит от 3.1)
└── 3.3 Интеграция стратегий (зависит от 3.2, 2.3)

Фаза 4: Система навигации
├── 4.1 Система патрулирования (зависит от 2.1)
├── 4.2 Поиск пути (зависит от 1.3)
└── 4.3 Система преследования (зависит от 4.1, 4.2)

Фаза 5: Групповое поведение  
├── 5.1 Групповая коммуникация (зависит от 1.2, 3.3)
├── 5.2 Координированные атаки (зависит от 5.1)
└── 5.3 Групповые тактики (зависит от 5.2)

Фаза 6: Интеграция и оптимизация
├── 6.1 Интеграция с боем (зависит от всех предыдущих фаз)
├── 6.2 Фабрика врагов (зависит от 6.1)
└── 6.3 Оптимизация (зависит от всех предыдущих фаз)
```

**Критический путь**: 1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 2.3 → 6.1 → 6.3

**Минимальные требования к тестированию**: 
- Unit тесты для каждого компонента ИИ и состояния
- Интеграционные тесты для взаимодействия систем ИИ  
- Тесты производительности при множественных врагах
- Минимальное покрытие: 90% для критических компонентов ИИ