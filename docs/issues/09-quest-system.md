# Issue #09: Квестовая система

## Описание
Реализация полноценной квестовой системы с различными типами заданий, цепочками квестов и системой наград.

## Цель
Добавить сюжетную составляющую и долгосрочные цели для мотивации игрока к исследованию мира и взаимодействию с NPC.

## Требования

### Типы квестов

#### Главные квесты
- [ ] **Основная сюжетная линия**:
  - [ ] Линейная последовательность ключевых заданий
  - [ ] Прогрессия по мирам и областям
  - [ ] Крупные награды и открытие нового контента
- [ ] **Эпические задания**:
  - [ ] Длительные многоэтапные квесты
  - [ ] Требуют высокого уровня и экипировки
  - [ ] Уникальные награды (легендарные предметы)

#### Побочные квесты
- [ ] **Задания от NPC**:
  - [ ] Помощь жителям различных миров
  - [ ] Решение локальных проблем
  - [ ] Исследование истории мира
- [ ] **Цепочки заданий**:
  - [ ] Связанные квесты с развивающимся сюжетом
  - [ ] Персональные истории NPC
  - [ ] Постепенное раскрытие тайн

#### Ежедневные задания
- [ ] **Повторяемые квесты**:
  - [ ] Обновляются каждый игровой день
  - [ ] Простые задачи (убить X врагов, собрать Y предметов)
  - [ ] Стабильный источник опыта и ресурсов
- [ ] **Еженедельные вызовы**:
  - [ ] Более сложные задания
  - [ ] Лучшие награды
  - [ ] Требуют планирования и подготовки

#### Достижения
- [ ] **Скрытые цели**:
  - [ ] Исследование всех областей мира
  - [ ] Коллекционирование предметов
  - [ ] Боевые достижения (убить 1000 врагов)
- [ ] **Особые награды**:
  - [ ] Титулы и звания
  - [ ] Уникальные предметы
  - [ ] Косметические улучшения

### Структура квеста

#### Основные компоненты
- [ ] **Уникальный идентификатор**: для системы сохранений
- [ ] **Название и описание**: понятная формулировка задачи
- [ ] **Цели и подцели**: четкие критерии выполнения
- [ ] **Условия активации**: требования для получения квеста
- [ ] **Система наград**: опыт, предметы, золото, доступы
- [ ] **Связи с другими квестами**: пререквизиты и последствия

#### Типы целей
- [ ] **Убийство врагов**:
  - [ ] Определенное количество конкретных врагов
  - [ ] Элитные враги или боссы
  - [ ] Враги в определенных локациях
- [ ] **Сбор предметов**:
  - [ ] Обычные предметы из мира
  - [ ] Редкие дропы с врагов
  - [ ] Квестовые предметы из определенных мест
- [ ] **Исследование**:
  - [ ] Посещение определенных областей
  - [ ] Активация порталов или механизмов
  - [ ] Поиск скрытых локаций
- [ ] **Взаимодействие с NPC**:
  - [ ] Доставка сообщений
  - [ ] Торговые операции
  - [ ] Диалоги и переговоры
- [ ] **Эскорт и защита**:
  - [ ] Сопровождение NPC до цели
  - [ ] Защита объектов от врагов
  - [ ] Ограничения по времени

### Состояния квестов
- [ ] **INACTIVE**: квест недоступен игроку
- [ ] **AVAILABLE**: можно взять у квестодателя
- [ ] **ACTIVE**: в процессе выполнения
- [ ] **COMPLETED**: выполнен, можно сдать
- [ ] **FINISHED**: получена награда
- [ ] **FAILED**: не удалось выполнить (опционально)

### Система наград

#### Типы наград
- [ ] **Опыт (XP)**:
  - [ ] Основной источник прогрессии
  - [ ] Масштабируется с уровнем квеста
  - [ ] Бонусы за цепочки квестов
- [ ] **Золото**:
  - [ ] Игровая валюта для торговли
  - [ ] Различные суммы в зависимости от сложности
- [ ] **Предметы**:
  - [ ] Оружие и броня
  - [ ] Расходуемые предметы
  - [ ] Уникальные квестовые награды
- [ ] **Доступы**:
  - [ ] Открытие новых областей
  - [ ] Доступ к новым NPC и услугам
  - [ ] Разблокировка следующих квестов
- [ ] **Титулы и достижения**:
  - [ ] Косметические награды
  - [ ] Показатели прогресса
  - [ ] Социальный статус

## Технические детали

### Архитектурные паттерны

#### ECS Components для квестовой системы
```python
# src/core/ecs/quest_components.py
class QuestComponent(Component):
    """Компонент квеста"""
    def __init__(self, quest_id: str, quest_type: str):
        self.quest_id = quest_id
        self.quest_type = quest_type  # MAIN, SIDE, DAILY, ACHIEVEMENT
        self.state = QuestState.INACTIVE
        self.objectives = []
        self.rewards = []
        self.prerequisites = []
        self.time_limit = -1  # -1 = без ограничения времени

class QuestGiverComponent(Component):
    """Компонент квестодателя"""
    def __init__(self):
        self.available_quests = []
        self.completed_quests = []
        self.dialogue_tree = None
        self.reputation_required = 0

class QuestObjectiveComponent(Component):
    """Компонент цели квеста"""
    def __init__(self, objective_type: str, target: str, required_quantity: int):
        self.objective_type = objective_type  # KILL, COLLECT, VISIT, TALK, ESCORT
        self.target = target
        self.required_quantity = required_quantity
        self.current_quantity = 0
        self.completed = False
        self.description = ""

class QuestProgressComponent(Component):
    """Компонент прогресса квестов игрока"""
    def __init__(self):
        self.active_quests = {}
        self.completed_quests = set()
        self.failed_quests = set()
        self.quest_log = []
```

#### Command Pattern для квестовых команд
```python
# src/quests/quest_commands.py
class QuestCommand(ABC):
    """Базовая команда для квестовых действий"""
    
    @abstractmethod
    def execute(self, quest_context: QuestContext) -> bool:
        pass
    
    @abstractmethod
    def undo(self, quest_context: QuestContext) -> bool:
        pass

class KillEnemiesCommand(QuestCommand):
    """Команда убийства врагов"""
    def __init__(self, enemy_type: str, count: int):
        self.enemy_type = enemy_type
        self.required_count = count
        self.killed_count = 0
    
    def execute(self, quest_context: QuestContext) -> bool:
        # Проверка выполнения через события
        if quest_context.event_type == "enemy_killed":
            enemy = quest_context.event_data.get("enemy")
            if enemy.enemy_type == self.enemy_type:
                self.killed_count += 1
                return self.killed_count >= self.required_count
        return False

class CollectItemsCommand(QuestCommand):
    """Команда сбора предметов"""
    def __init__(self, item_id: str, count: int):
        self.item_id = item_id
        self.required_count = count
        self.collected_count = 0
    
    def execute(self, quest_context: QuestContext) -> bool:
        player = quest_context.player
        inventory_comp = player.get_component(InventoryComponent)
        
        # Подсчет предметов в инвентаре
        current_count = inventory_comp.count_item(self.item_id)
        self.collected_count = current_count
        
        return self.collected_count >= self.required_count

class DeliverItemCommand(QuestCommand):
    """Команда доставки предмета"""
    def __init__(self, item_id: str, npc_id: str):
        self.item_id = item_id
        self.npc_id = npc_id
        self.delivered = False
    
    def execute(self, quest_context: QuestContext) -> bool:
        if quest_context.event_type == "item_delivered":
            event_data = quest_context.event_data
            if (event_data.get("item_id") == self.item_id and 
                event_data.get("npc_id") == self.npc_id):
                self.delivered = True
                return True
        return False

class CompositeQuestCommand(QuestCommand):
    """Составная команда для сложных квестов"""
    def __init__(self, commands: List[QuestCommand], require_all: bool = True):
        self.commands = commands
        self.require_all = require_all  # True = все команды, False = любая команда
    
    def execute(self, quest_context: QuestContext) -> bool:
        completed_commands = []
        
        for command in self.commands:
            if command.execute(quest_context):
                completed_commands.append(command)
        
        if self.require_all:
            return len(completed_commands) == len(self.commands)
        else:
            return len(completed_commands) > 0
```

#### State Pattern для состояний квестов
```python
# src/quests/quest_states.py
class QuestState(ABC):
    """Базовое состояние квеста"""
    
    @abstractmethod
    def enter(self, quest: Entity):
        pass
    
    @abstractmethod
    def update(self, quest: Entity, quest_context: QuestContext) -> Optional[QuestState]:
        pass
    
    @abstractmethod
    def exit(self, quest: Entity):
        pass

class InactiveQuestState(QuestState):
    """Неактивный квест"""
    def enter(self, quest: Entity):
        quest_comp = quest.get_component(QuestComponent)
        quest_comp.state = "INACTIVE"
    
    def update(self, quest: Entity, quest_context: QuestContext) -> Optional[QuestState]:
        # Проверка условий активации
        if self._check_prerequisites(quest, quest_context.player):
            return AvailableQuestState()
        return None

class AvailableQuestState(QuestState):
    """Доступный для получения квест"""
    def enter(self, quest: Entity):
        quest_comp = quest.get_component(QuestComponent)
        quest_comp.state = "AVAILABLE"
    
    def update(self, quest: Entity, quest_context: QuestContext) -> Optional[QuestState]:
        # Проверка получения квеста игроком
        if quest_context.event_type == "quest_accepted":
            if quest_context.event_data.get("quest_id") == quest.get_component(QuestComponent).quest_id:
                return ActiveQuestState()
        return None

class ActiveQuestState(QuestState):
    """Активный квест"""
    def enter(self, quest: Entity):
        quest_comp = quest.get_component(QuestComponent)
        quest_comp.state = "ACTIVE"
        
        # Добавление в активные квесты игрока
        player = quest_context.player
        progress_comp = player.get_component(QuestProgressComponent)
        progress_comp.active_quests[quest_comp.quest_id] = quest
    
    def update(self, quest: Entity, quest_context: QuestContext) -> Optional[QuestState]:
        quest_comp = quest.get_component(QuestComponent)
        
        # Проверка выполнения всех целей
        all_completed = True
        for objective in quest_comp.objectives:
            if not objective.execute(quest_context):
                all_completed = False
        
        if all_completed:
            return CompletedQuestState()
        
        # Проверка провала квеста
        if self._check_quest_failure(quest, quest_context):
            return FailedQuestState()
        
        return None

class CompletedQuestState(QuestState):
    """Выполненный квест"""
    def enter(self, quest: Entity):
        quest_comp = quest.get_component(QuestComponent)
        quest_comp.state = "COMPLETED"
        
        # Выдача наград
        self._give_rewards(quest, quest_context.player)

class FailedQuestState(QuestState):
    """Проваленный квест"""
    def enter(self, quest: Entity):
        quest_comp = quest.get_component(QuestComponent)
        quest_comp.state = "FAILED"
```

#### Observer Pattern для отслеживания прогресса
```python
# src/quests/quest_tracker.py
class QuestTracker(System):
    """Система отслеживания квестов как Observer"""
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        
        # Подписка на игровые события
        self.event_system.subscribe("enemy_killed", self.handle_enemy_killed)
        self.event_system.subscribe("item_collected", self.handle_item_collected)
        self.event_system.subscribe("area_visited", self.handle_area_visited)
        self.event_system.subscribe("npc_talked", self.handle_npc_interaction)
        self.event_system.subscribe("item_delivered", self.handle_item_delivery)
    
    def handle_enemy_killed(self, event: EnemyKilledEvent):
        """Обработка убийства врага для квестов"""
        player = event.killer
        progress_comp = player.get_component(QuestProgressComponent)
        
        quest_context = QuestContext(
            player=player,
            event_type="enemy_killed",
            event_data={"enemy": event.enemy, "enemy_type": event.enemy.enemy_type}
        )
        
        # Обновление всех активных квестов
        for quest_id, quest in progress_comp.active_quests.items():
            self._update_quest_progress(quest, quest_context)
    
    def handle_item_collected(self, event: ItemCollectedEvent):
        """Обработка сбора предметов для квестов"""
        player = event.collector
        progress_comp = player.get_component(QuestProgressComponent)
        
        quest_context = QuestContext(
            player=player,
            event_type="item_collected",
            event_data={"item": event.item, "item_id": event.item.item_id}
        )
        
        for quest_id, quest in progress_comp.active_quests.items():
            self._update_quest_progress(quest, quest_context)
    
    def _update_quest_progress(self, quest: Entity, quest_context: QuestContext):
        """Обновление прогресса квеста"""
        quest_comp = quest.get_component(QuestComponent)
        
        # Проверка выполнения целей
        for objective in quest_comp.objectives:
            if not objective.completed:
                if objective.execute(quest_context):
                    objective.completed = True
                    self._emit_objective_completed_event(quest, objective)
        
        # Проверка завершения квеста
        if all(obj.completed for obj in quest_comp.objectives):
            self._complete_quest(quest, quest_context.player)
    
    def _complete_quest(self, quest: Entity, player: Entity):
        """Завершение квеста"""
        quest_comp = quest.get_component(QuestComponent)
        progress_comp = player.get_component(QuestProgressComponent)
        
        # Перемещение из активных в завершенные
        if quest_comp.quest_id in progress_comp.active_quests:
            del progress_comp.active_quests[quest_comp.quest_id]
            progress_comp.completed_quests.add(quest_comp.quest_id)
        
        # Выдача наград
        self._give_quest_rewards(quest, player)
        
        # Событие завершения квеста
        self.event_system.emit(QuestCompletedEvent(player, quest))
```

#### Factory Pattern для создания квестов
```python
# src/quests/quest_factory.py
class QuestFactory(ABC):
    """Абстрактная фабрика квестов"""
    
    @abstractmethod
    def create_quest(self, quest_data: dict) -> Entity:
        pass

class StandardQuestFactory(QuestFactory):
    """Стандартная фабрика квестов"""
    def create_quest(self, quest_data: dict) -> Entity:
        entity = Entity()
        
        # Базовый компонент квеста
        quest_comp = QuestComponent(
            quest_data['id'],
            quest_data['type']
        )
        
        # Создание целей квеста
        objectives = []
        for obj_data in quest_data['objectives']:
            objective = self._create_objective(obj_data)
            objectives.append(objective)
        
        quest_comp.objectives = objectives
        quest_comp.rewards = quest_data.get('rewards', [])
        quest_comp.prerequisites = quest_data.get('prerequisites', [])
        
        entity.add_component(quest_comp)
        return entity
    
    def _create_objective(self, obj_data: dict) -> QuestCommand:
        """Создание цели квеста"""
        obj_type = obj_data['type']
        
        if obj_type == "kill":
            return KillEnemiesCommand(obj_data['target'], obj_data['count'])
        elif obj_type == "collect":
            return CollectItemsCommand(obj_data['item_id'], obj_data['count'])
        elif obj_type == "deliver":
            return DeliverItemCommand(obj_data['item_id'], obj_data['npc_id'])
        elif obj_type == "composite":
            sub_objectives = [self._create_objective(sub_obj) for sub_obj in obj_data['objectives']]
            return CompositeQuestCommand(sub_objectives, obj_data.get('require_all', True))
        
        return None

class DynamicQuestFactory(QuestFactory):
    """Фабрика динамических квестов"""
    def create_quest(self, quest_template: str, player_level: int, world_context: dict) -> Entity:
        # Генерация квеста на основе шаблона и контекста
        quest_data = self._generate_quest_data(quest_template, player_level, world_context)
        return StandardQuestFactory().create_quest(quest_data)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── quest_components.py       # Компоненты квестовой системы
├── quests/
│   ├── quest_commands.py         # Команды квестов (Command Pattern)
│   ├── quest_states.py           # Состояния квестов (State Pattern)
│   ├── quest_tracker.py          # Отслеживание квестов (Observer Pattern)
│   ├── quest_factory.py          # Фабрика квестов (Factory Pattern)
│   ├── quest_system.py           # Основная система квестов (ECS System)
│   └── quest_manager.py          # Управление квестами
├── ui/
│   ├── quest_journal.py          # Журнал квестов
│   ├── quest_tracker_ui.py       # UI отслеживания прогресса
│   └── quest_notifications.py    # Уведомления о квестах
├── events/
│   └── quest_events.py           # События квестовой системы
└── data/
    ├── quests/                   # Конфигурации квестов
    └── quest_templates/          # Шаблоны для динамических квестов
```

### Файлы для создания/изменения
- `src/core/ecs/quest_components.py` - компоненты квестовой системы
- `src/quests/quest_commands.py` - команды квестов (Command Pattern)
- `src/quests/quest_states.py` - состояния квестов (State Pattern)
- `src/quests/quest_tracker.py` - отслеживание квестов (Observer Pattern)
- `src/quests/quest_factory.py` - фабрика квестов (Factory Pattern)
- `src/quests/quest_system.py` - основная система квестов (ECS System)
- `src/ui/quest_journal.py` - журнал квестов
- `src/ui/quest_tracker_ui.py` - UI отслеживания прогресса
- `src/events/quest_events.py` - события квестовой системы
- `src/entities/npc.py` - интеграция с NPC

### Архитектура квестовой системы
```python
class Quest:
    def __init__(self, quest_id, name, description, objectives, rewards):
        self.id = quest_id
        self.name = name
        self.description = description
        self.objectives = objectives
        self.rewards = rewards
        self.state = QuestState.INACTIVE
        self.progress = {}
        
    def check_completion(self):
        return all(obj.is_completed() for obj in self.objectives)
        
class QuestObjective:
    def __init__(self, obj_type, target, quantity, description):
        self.type = obj_type  # KILL, COLLECT, VISIT, TALK
        self.target = target
        self.required_quantity = quantity
        self.current_quantity = 0
        self.description = description
        
    def is_completed(self):
        return self.current_quantity >= self.required_quantity

class QuestManager:
    def __init__(self):
        self.active_quests = []
        self.completed_quests = []
        self.available_quests = []
        
    def update_progress(self, event_type, target, quantity=1):
        for quest in self.active_quests:
            quest.update_progress(event_type, target, quantity)
```

### Конфигурация
```ini
[QUEST_SYSTEM]
max_active_quests = 10
auto_track_new_quests = true
show_objective_markers = true

[QUEST_REWARDS]
xp_base_multiplier = 1.0
gold_base_amount = 50
item_drop_chance = 30

[DAILY_QUESTS]
reset_time = 00:00
max_daily_quests = 5
completion_bonus = 1.2
```

### Интеграция с другими системами
- [ ] **NPC система**: квестодатели и получатели
- [ ] **Event система**: активация квестов через триггеры
- [ ] **Система врагов**: отслеживание убийств
- [ ] **Инвентарь**: квестовые предметы и награды
- [ ] **Прогрессия**: опыт и уровни
- [ ] **Система сохранений**: состояние квестов

### Интерфейс квестов

#### Журнал квестов (клавиша Q)
- [ ] **Список активных квестов**:
  - [ ] Название и краткое описание
  - [ ] Прогресс выполнения целей
  - [ ] Предполагаемые награды
- [ ] **Категории**:
  - [ ] Главные квесты
  - [ ] Побочные квесты
  - [ ] Ежедневные задания
  - [ ] Завершенные квесты
- [ ] **Детальная информация**:
  - [ ] Полное описание квеста
  - [ ] Список всех целей
  - [ ] История диалогов

#### Трекер квестов
- [ ] **Отображение на экране**:
  - [ ] Список активных целей
  - [ ] Прогресс в реальном времени
  - [ ] Направление к цели (опционально)
- [ ] **Уведомления**:
  - [ ] Получение нового квеста
  - [ ] Выполнение цели
  - [ ] Завершение квеста

## Критерии готовности
- [ ] Минимум 10 различных квестов реализованы
- [ ] Все типы целей функциональны
- [ ] Система наград работает корректно
- [ ] Журнал квестов отображает информацию
- [ ] Прогресс сохраняется между сессиями
- [ ] Интеграция с NPC функциональна
- [ ] Цепочки квестов работают правильно

## Приоритет
**Средний** - Важно для долгосрочного интереса

## Зависимости
- Issue #05 (Враги) - для боевых квестов
- Issue #07 (Event boxes) - для активации квестов
- Issue #08 (Инвентарь) - для квестовых предметов
- Текущая система NPC

## Примеры квестов

### Главный квест: "Пробуждение стихий"
- **Описание**: Изучите три стихии магии
- **Цели**:
  - Найти Посох Огня в Подземном мире
  - Получить Кристалл Холода в Ледяном мире
  - Активировать Алтарь Молний в Лесном мире
- **Награда**: Доступ к комбинированной магии

### Побочный квест: "Потерянный караван"
- **Описание**: Найдите пропавший торговый караван
- **Цели**:
  - Найти следы каравана (3 локации)
  - Убить разбойников (5 врагов)
  - Вернуть украденные товары торговцу
- **Награда**: 200 золота, редкое оружие

## Примерное время реализации
4-5 недель

## Связанные issues
- #05 (Враги) - боевые квесты
- #06 (Прогрессия) - опыт за квесты
- #07 (Event boxes) - активация квестов
- #08 (Инвентарь) - квестовые предметы

---

## Подзадачи для реализации

### 📋 Фаза 1: Базовая архитектура квестовой системы
**Цель**: Создание ECS компонентов и основы квестовой системы

#### 1.1 ECS компоненты квестов
- [ ] Создать `src/core/ecs/quest_components.py` - QuestComponent, QuestGiverComponent
- [ ] Создать QuestObjectiveComponent, QuestProgressComponent
- [ ] Создать `test_quest_components.py` - unit тесты компонентов квестов
- [ ] Все компоненты квестов работают с базовой функциональностью

#### 1.2 События квестовой системы
- [ ] Создать `src/events/quest_events.py` - QuestEvent, QuestAcceptedEvent, QuestCompletedEvent
- [ ] Создать QuestProgressEvent, QuestFailedEvent
- [ ] Создать `test_quest_events.py` - тестирование событий квестов
- [ ] События квестов корректно обрабатываются системой

#### 1.3 Базовая система квестов как ECS System
- [ ] Создать `src/quests/quest_system.py` - QuestSystem (ECS System)
- [ ] Управление состояниями квестов и прогрессом
- [ ] Создать `test_quest_system.py` - тестирование системы квестов
- [ ] Система корректно управляет квестами и их состояниями

### 🎯 Фаза 2: Command Pattern для целей квестов
**Цель**: Реализация различных типов квестовых целей

#### 2.1 Базовые команды квестов
- [ ] Создать `src/quests/quest_commands.py` - QuestCommand, KillEnemiesCommand
- [ ] Создать CollectItemsCommand, DeliverItemCommand
- [ ] Создать `test_quest_commands.py` - тестирование команд квестов
- [ ] Все базовые типы квестовых целей выполняются корректно

#### 2.2 Составные команды квестов
- [ ] Создать CompositeQuestCommand для сложных квестов
- [ ] Логика "И" и "ИЛИ" для множественных целей
- [ ] Создать `test_composite_quests.py` - тестирование составных квестов
- [ ] Сложные квесты с множественными целями работают правильно

#### 2.3 Расширенные команды квестов
- [ ] Создать VisitAreaCommand, TalkToNPCCommand, EscortCommand
- [ ] Создать UseItemCommand, CraftItemCommand
- [ ] Создать `test_advanced_quest_commands.py` - тестирование расширенных команд
- [ ] Все типы квестовых целей из требований реализованы

### 🔄 Фаза 3: State Pattern для состояний квестов
**Цель**: Управление жизненным циклом квестов

#### 3.1 Базовые состояния квестов
- [ ] Создать `src/quests/quest_states.py` - QuestState, InactiveQuestState, AvailableQuestState
- [ ] Создать ActiveQuestState, CompletedQuestState, FailedQuestState
- [ ] Создать `test_quest_states.py` - тестирование состояний квестов
- [ ] Все состояния квестов корректно переключаются

#### 3.2 Машина состояний квестов
- [ ] Создать QuestStateMachine для управления переходами
- [ ] Система условий и триггеров перехода
- [ ] Создать `test_quest_state_machine.py` - тестирование машины состояний
- [ ] Квесты корректно проходят весь жизненный цикл

#### 3.3 Интеграция состояний с системой квестов
- [ ] Обновить QuestSystem для работы с машиной состояний
- [ ] Автоматическое определение доступности квестов
- [ ] Создать `test_quest_state_integration.py` - тестирование интеграции
- [ ] Квесты автоматически становятся доступными при выполнении условий

### 📊 Фаза 4: Observer Pattern для отслеживания прогресса
**Цель**: Автоматическое отслеживание выполнения квестов

#### 4.1 Система отслеживания квестов как Observer
- [ ] Создать `src/quests/quest_tracker.py` - QuestTracker (System + Observer)
- [ ] Подписка на игровые события: убийства, сбор предметов, диалоги
- [ ] Создать `test_quest_tracker.py` - тестирование отслеживания квестов
- [ ] Прогресс квестов автоматически обновляется при игровых действиях

#### 4.2 Обработчики событий для разных типов целей
- [ ] Создать специализированные обработчики для каждого типа цели
- [ ] Интеграция с системами врагов, инвентаря, NPC
- [ ] Создать `test_quest_event_handlers.py` - тестирование обработчиков
- [ ] Все типы квестовых целей корректно отслеживаются

#### 4.3 Система уведомлений о прогрессе
- [ ] Уведомления о выполнении целей и завершении квестов
- [ ] Интеграция с UI системой
- [ ] Создать `test_quest_notifications.py` - тестирование уведомлений
- [ ] Игрок получает обратную связь о прогрессе квестов

### 🏭 Фаза 5: Factory Pattern для создания квестов
**Цель**: Создание различных типов квестов

#### 5.1 Базовая фабрика квестов
- [ ] Создать `src/quests/quest_factory.py` - QuestFactory, StandardQuestFactory
- [ ] Создание квестов из конфигурационных данных
- [ ] Создать `test_quest_factory.py` - тестирование фабрики квестов
- [ ] Фабрика корректно создает все типы квестов

#### 5.2 Динамическая фабрика квестов
- [ ] Создать DynamicQuestFactory для генерации квестов по шаблонам
- [ ] Система случайной генерации ежедневных квестов
- [ ] Создать `test_dynamic_quests.py` - тестирование динамических квестов
- [ ] Ежедневные квесты автоматически генерируются

#### 5.3 Загрузка квестов из конфигурации
- [ ] Система загрузки квестов из JSON/YAML файлов
- [ ] Валидация структуры и параметров квестов
- [ ] Создать `test_quest_loading.py` - тестирование загрузки квестов
- [ ] Квесты корректно загружаются из файлов конфигурации

### 💰 Фаза 6: Система наград и типы квестов
**Цель**: Реализация всех типов квестов и их наград

#### 6.1 Система наград квестов
- [ ] Создать `src/quests/quest_rewards.py` - система выдачи наград
- [ ] Интеграция с системами опыта, инвентаря, прогрессии
- [ ] Создать `test_quest_rewards.py` - тестирование наград
- [ ] Награды корректно выдаются при завершении квестов

#### 6.2 Главные и побочные квесты
- [ ] Реализовать MainQuestFactory для сюжетных квестов
- [ ] Создать SideQuestFactory для побочных заданий
- [ ] Создать `test_main_side_quests.py` - тестирование типов квестов
- [ ] Главные и побочные квесты имеют соответствующие характеристики

#### 6.3 Ежедневные квесты и достижения
- [ ] Реализовать DailyQuestFactory с системой обновления
- [ ] Создать AchievementFactory для скрытых целей
- [ ] Создать `test_daily_achievements.py` - тестирование специальных квестов
- [ ] Ежедневные квесты и достижения работают корректно

### 🎮 Фаза 7: Пользовательский интерфейс квестов
**Цель**: UI для управления квестами и отслеживания прогресса

#### 7.1 Журнал квестов
- [ ] Создать `src/ui/quest_journal.py` - окно журнала квестов (клавиша Q)
- [ ] Отображение активных, завершенных и доступных квестов
- [ ] Создать `test_quest_journal.py` - тестирование журнала квестов
- [ ] Удобный интерфейс для просмотра квестов и их прогресса

#### 7.2 Трекер квестов в игре
- [ ] Создать `src/ui/quest_tracker_ui.py` - отображение активных целей на экране
- [ ] Система выбора отслеживаемых квестов
- [ ] Создать `test_quest_tracker_ui.py` - тестирование трекера
- [ ] Игрок видит прогресс активных квестов в реальном времени

#### 7.3 Диалоги с квестодателями
- [ ] Интеграция с системой NPC для выдачи квестов
- [ ] Система диалогов для получения и сдачи квестов
- [ ] Создать `test_quest_dialogs.py` - тестирование диалогов квестов
- [ ] NPC корректно выдают и принимают квесты

### 🔗 Фаза 8: Цепочки квестов и интеграция
**Цель**: Сложные квестовые линии и финальная интеграция

#### 8.1 Система цепочек квестов
- [ ] Создать QuestChainManager для управления связанными квестами
- [ ] Система пререквизитов и зависимостей между квестами
- [ ] Создать `test_quest_chains.py` - тестирование цепочек квестов
- [ ] Квесты корректно открываются в зависимости от выполненных

#### 8.2 Интеграция с другими системами
- [ ] Связать квесты с системой Event Boxes для активации
- [ ] Интеграция с системой врагов для боевых квестов
- [ ] Создать `test_quest_integration.py` - интеграционные тесты
- [ ] Квесты корректно работают со всеми игровыми системами

#### 8.3 Конфигурация и примеры квестов
- [ ] Добавить настройки квестов в `config.ini`
- [ ] Создать примеры квестов из требований ("Пробуждение стихий", "Потерянный караван")
- [ ] Создать `test_example_quests.py` - тестирование примеров
- [ ] Создать документацию по созданию квестов в `CLAUDE.md`
- [ ] Полная система квестов готова с примерами

---

## 🌳 Дерево зависимостей подзадач

```
Фаза 1: Базовая архитектура квестов
├── 1.1 ECS компоненты квестов
├── 1.2 События квестовой системы (зависит от 1.1)
└── 1.3 Базовая система квестов (зависит от 1.1, 1.2)

Фаза 2: Command Pattern для целей
├── 2.1 Базовые команды (зависит от 1.1)
├── 2.2 Составные команды (зависит от 2.1)
└── 2.3 Расширенные команды (зависит от 2.2)

Фаза 3: State Pattern для состояний
├── 3.1 Базовые состояния (зависит от 1.1)
├── 3.2 Машина состояний (зависит от 3.1)
└── 3.3 Интеграция состояний (зависит от 3.2, 1.3)

Фаза 4: Observer Pattern для отслеживания
├── 4.1 Система отслеживания (зависит от 1.2, 2.1)
├── 4.2 Обработчики событий (зависит от 4.1, Issue #05, #08)
└── 4.3 Уведомления (зависит от 4.2)

Фаза 5: Factory Pattern для создания
├── 5.1 Базовая фабрика (зависит от 2.3, 3.1)
├── 5.2 Динамическая фабрика (зависит от 5.1)
└── 5.3 Загрузка из конфигурации (зависит от 5.2)

Фаза 6: Система наград и типы квестов
├── 6.1 Система наград (зависит от 5.1, Issue #06, #08)
├── 6.2 Главные и побочные квесты (зависит от 6.1)
└── 6.3 Ежедневные квесты (зависит от 6.2)

Фаза 7: UI квестов
├── 7.1 Журнал квестов (зависит от 3.3)
├── 7.2 Трекер квестов (зависит от 7.1, 4.3)
└── 7.3 Диалоги NPC (зависит от 7.1)

Фаза 8: Интеграция и цепочки
├── 8.1 Цепочки квестов (зависит от 6.3, 3.3)
├── 8.2 Интеграция (зависит от всех предыдущих фаз, Issue #07)
└── 8.3 Конфигурация (зависит от всех предыдущих фаз)
```

**Критический путь**: 1.1 → 1.2 → 1.3 → 2.1 → 3.1 → 4.1 → 5.1 → 7.1 → 8.2 → 8.3

**Минимальные требования к тестированию**: 
- Unit тесты для каждого компонента квестов и типа цели
- Интеграционные тесты для взаимодействия с другими системами
- Тесты полного жизненного цикла квестов
- Минимальное покрытие: 90% для критических компонентов квестовой системы