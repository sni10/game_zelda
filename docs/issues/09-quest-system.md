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