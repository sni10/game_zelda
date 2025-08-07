# Issue #06: Дерево навыков и система прогрессии

## Описание
Реализация системы прокачки персонажа с деревом навыков, уровнями и распределением очков способностей.

## Цель
Добавить RPG-элементы прогрессии для долгосрочной мотивации игрока и кастомизации стиля игры.

## Требования

### Система опыта и уровней
- [ ] **Опыт (XP)**:
  - [ ] Получение за убийство врагов
  - [ ] Получение за выполнение квестов
  - [ ] Получение за исследование новых областей
  - [ ] Получение за первое использование предметов
- [ ] **Уровни**:
  - [ ] Стартовый уровень: 1
  - [ ] Максимальный уровень: 50
  - [ ] Прогрессивная шкала опыта (каждый уровень требует больше XP)
  - [ ] Очки навыков: 1 за уровень
- [ ] **Индикация прогресса**:
  - [ ] Полоска опыта в UI
  - [ ] Уведомления о повышении уровня
  - [ ] Счетчик доступных очков навыков

### Дерево навыков (4 ветки по 3 навыка)

#### Ветка магии
- [ ] **Увеличение маны**:
  - [ ] Уровень 1: +20 максимальной маны
  - [ ] Уровень 2: +40 максимальной маны
  - [ ] Уровень 3: +60 максимальной маны
- [ ] **Усиление магического урона**:
  - [ ] Уровень 1: +25% урон от заклинаний
  - [ ] Уровень 2: +50% урон от заклинаний
  - [ ] Уровень 3: +75% урон от заклинаний
- [ ] **Продление действия заклинаний**:
  - [ ] Уровень 1: +50% длительность эффектов
  - [ ] Уровень 2: +100% длительность эффектов
  - [ ] Уровень 3: +150% длительность эффектов

#### Ветка ближнего боя
- [ ] **Увеличение урона ближнего оружия**:
  - [ ] Уровень 1: +20% урон мечей
  - [ ] Уровень 2: +40% урон мечей
  - [ ] Уровень 3: +60% урон мечей
- [ ] **Скорость атак**:
  - [ ] Уровень 1: +15% скорость атаки
  - [ ] Уровень 2: +30% скорость атаки
  - [ ] Уровень 3: +45% скорость атаки
- [ ] **Критический урон**:
  - [ ] Уровень 1: 5% шанс крита, +50% урон
  - [ ] Уровень 2: 10% шанс крита, +75% урон
  - [ ] Уровень 3: 15% шанс крита, +100% урон

#### Ветка дальнего боя
- [ ] **Увеличение урона дальнего оружия**:
  - [ ] Уровень 1: +25% урон луков/арбалетов
  - [ ] Уровень 2: +50% урон луков/арбалетов
  - [ ] Уровень 3: +75% урон луков/арбалетов
- [ ] **Точность и дальность стрельбы**:
  - [ ] Уровень 1: +20% дальность, меньше разброса
  - [ ] Уровень 2: +40% дальность, еще меньше разброса
  - [ ] Уровень 3: +60% дальность, идеальная точность
- [ ] **Скорость перезарядки**:
  - [ ] Уровень 1: +20% скорость перезарядки
  - [ ] Уровень 2: +40% скорость перезарядки
  - [ ] Уровень 3: +60% скорость перезарядки

#### Ветка выносливости
- [ ] **Увеличение здоровья (HP)**:
  - [ ] Уровень 1: +25 максимального HP
  - [ ] Уровень 2: +50 максимального HP
  - [ ] Уровень 3: +75 максимального HP
- [ ] **Регенерация здоровья**:
  - [ ] Уровень 1: 1 HP каждые 10 секунд
  - [ ] Уровень 2: 1 HP каждые 5 секунд
  - [ ] Уровень 3: 1 HP каждые 3 секунды
- [ ] **Устойчивость к дебафам**:
  - [ ] Уровень 1: -25% длительность дебафов
  - [ ] Уровень 2: -50% длительность дебафов
  - [ ] Уровень 3: -75% длительность дебафов

## Технические детали

### Архитектурные паттерны

#### ECS Components для системы прогрессии
```python
# src/core/ecs/progression_components.py
class ExperienceComponent(Component):
    """Компонент опыта"""
    def __init__(self):
        self.current_level = 1
        self.current_xp = 0
        self.xp_to_next_level = 100
        self.total_xp = 0
        self.available_skill_points = 0

class SkillTreeComponent(Component):
    """Компонент дерева навыков"""
    def __init__(self):
        self.skill_branches = {
            'magic': MagicSkillBranch(),
            'melee': MeleeSkillBranch(),
            'ranged': RangedSkillBranch(),
            'vitality': VitalitySkillBranch()
        }
        self.learned_skills = {}

class SkillComponent(Component):
    """Компонент отдельного навыка"""
    def __init__(self, skill_id: str, branch: str, max_level: int = 3):
        self.skill_id = skill_id
        self.branch = branch
        self.current_level = 0
        self.max_level = max_level
        self.prerequisites = []
        self.effects = []

class StatModifierComponent(Component):
    """Компонент модификаторов характеристик от навыков"""
    def __init__(self):
        self.modifiers = {
            'max_hp': 0,
            'max_mana': 0,
            'damage_multiplier': 1.0,
            'attack_speed_multiplier': 1.0,
            'magic_damage_multiplier': 1.0,
            'defense_multiplier': 1.0
        }
```

#### Observer Pattern для системы опыта
```python
# src/events/progression_events.py
class ExperienceGainedEvent(GameEvent):
    """Событие получения опыта"""
    def __init__(self, entity: Entity, xp_amount: int, source: str):
        super().__init__("experience_gained")
        self.entity = entity
        self.xp_amount = xp_amount
        self.source = source  # "enemy_kill", "quest_complete", "area_discovery"

class LevelUpEvent(GameEvent):
    """Событие повышения уровня"""
    def __init__(self, entity: Entity, new_level: int, skill_points_gained: int):
        super().__init__("level_up")
        self.entity = entity
        self.new_level = new_level
        self.skill_points_gained = skill_points_gained

class SkillLearnedEvent(GameEvent):
    """Событие изучения навыка"""
    def __init__(self, entity: Entity, skill_id: str, skill_level: int):
        super().__init__("skill_learned")
        self.entity = entity
        self.skill_id = skill_id
        self.skill_level = skill_level

# Система прогрессии как Observer
class ProgressionSystem(System):
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        
        # Подписка на события для получения опыта
        self.event_system.subscribe("enemy_killed", self.handle_enemy_killed)
        self.event_system.subscribe("quest_completed", self.handle_quest_completed)
        self.event_system.subscribe("area_discovered", self.handle_area_discovered)
        self.event_system.subscribe("spell_cast", self.handle_spell_cast)
        self.event_system.subscribe("weapon_used", self.handle_weapon_used)
    
    def handle_enemy_killed(self, event: EnemyKilledEvent):
        """Обработка убийства врага"""
        player = event.killer
        if player:
            xp_reward = self._calculate_enemy_xp(event.enemy)
            self.grant_experience(player, xp_reward, "enemy_kill")
    
    def handle_spell_cast(self, event: SpellCastEvent):
        """Обработка применения заклинания для прокачки магии"""
        caster = event.caster
        spell_xp = 5  # базовый опыт за заклинание
        self.grant_skill_experience(caster, "magic", spell_xp)
```

#### Strategy Pattern для различных типов навыков
```python
# src/progression/skill_strategies.py
class SkillStrategy(ABC):
    """Стратегия применения навыка"""
    
    @abstractmethod
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        pass
    
    @abstractmethod
    def remove_skill_effect(self, entity: Entity, skill_level: int):
        pass

class PassiveSkillStrategy(SkillStrategy):
    """Стратегия пассивного навыка (постоянный эффект)"""
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        # Применяем постоянный модификатор
        modifier_comp = entity.get_component(StatModifierComponent)
        if modifier_comp:
            self._apply_stat_bonus(modifier_comp, skill_level)

class ActiveSkillStrategy(SkillStrategy):
    """Стратегия активного навыка (способность)"""
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        # Добавляем новую способность
        ability_comp = entity.get_component(AbilityComponent)
        if ability_comp:
            new_ability = self._create_ability(skill_level)
            ability_comp.available_abilities.append(new_ability)

class MagicSkillStrategy(PassiveSkillStrategy):
    """Стратегия навыков магии"""
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        magic_comp = entity.get_component(MagicComponent)
        modifier_comp = entity.get_component(StatModifierComponent)
        
        if magic_comp and modifier_comp:
            # Увеличение маны
            mana_bonus = skill_level * 20
            modifier_comp.modifiers['max_mana'] += mana_bonus
            magic_comp.max_mana += mana_bonus
            
            # Увеличение магического урона
            magic_damage_bonus = 1.0 + (skill_level * 0.25)
            modifier_comp.modifiers['magic_damage_multiplier'] *= magic_damage_bonus

class MeleeSkillStrategy(PassiveSkillStrategy):
    """Стратегия навыков ближнего боя"""
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        modifier_comp = entity.get_component(StatModifierComponent)
        
        if modifier_comp:
            # Увеличение урона ближнего боя
            damage_bonus = 1.0 + (skill_level * 0.20)
            modifier_comp.modifiers['damage_multiplier'] *= damage_bonus
            
            # Увеличение скорости атаки
            speed_bonus = 1.0 + (skill_level * 0.15)
            modifier_comp.modifiers['attack_speed_multiplier'] *= speed_bonus

class VitalitySkillStrategy(PassiveSkillStrategy):
    """Стратегия навыков выносливости"""
    def apply_skill_effect(self, entity: Entity, skill_level: int):
        health_comp = entity.get_component(HealthComponent)
        modifier_comp = entity.get_component(StatModifierComponent)
        
        if health_comp and modifier_comp:
            # Увеличение максимального здоровья
            hp_bonus = skill_level * 25
            modifier_comp.modifiers['max_hp'] += hp_bonus
            health_comp.max_hp += hp_bonus
            
            # Регенерация здоровья
            if skill_level >= 2:
                regen_comp = entity.get_component(RegenerationComponent)
                if not regen_comp:
                    regen_comp = RegenerationComponent()
                    entity.add_component(regen_comp)
                regen_comp.hp_regen_rate = skill_level * 0.5
```

#### Decorator Pattern для бонусов от навыков
```python
# src/progression/skill_decorators.py
class SkillBonusDecorator(ABC):
    """Декоратор для бонусов от навыков"""
    def __init__(self, base_component: Component):
        self._base_component = base_component
    
    @abstractmethod
    def get_modified_value(self, attribute: str):
        pass

class WeaponSkillDecorator(SkillBonusDecorator):
    """Декоратор бонусов к оружию от навыков"""
    def __init__(self, weapon_component: WeaponComponent, skill_level: int):
        super().__init__(weapon_component)
        self.skill_level = skill_level
    
    def get_modified_value(self, attribute: str):
        base_value = getattr(self._base_component, attribute)
        
        if attribute == 'base_damage':
            # Увеличение урона от навыка
            damage_bonus = 1.0 + (self.skill_level * 0.2)
            return base_value * damage_bonus
        elif attribute == 'attack_speed':
            # Увеличение скорости атаки
            speed_bonus = 1.0 + (self.skill_level * 0.15)
            return base_value * speed_bonus
        
        return base_value

class MagicSkillDecorator(SkillBonusDecorator):
    """Декоратор бонусов к магии от навыков"""
    def __init__(self, magic_component: MagicComponent, skill_level: int):
        super().__init__(magic_component)
        self.skill_level = skill_level
    
    def get_modified_value(self, attribute: str):
        base_value = getattr(self._base_component, attribute)
        
        if attribute == 'max_mana':
            mana_bonus = self.skill_level * 20
            return base_value + mana_bonus
        elif attribute == 'mana_regen_rate':
            regen_bonus = 1.0 + (self.skill_level * 0.3)
            return base_value * regen_bonus
        
        return base_value

class HealthSkillDecorator(SkillBonusDecorator):
    """Декоратор бонусов к здоровью от навыков"""
    def __init__(self, health_component: HealthComponent, skill_level: int):
        super().__init__(health_component)
        self.skill_level = skill_level
    
    def get_modified_value(self, attribute: str):
        base_value = getattr(self._base_component, attribute)
        
        if attribute == 'max_hp':
            hp_bonus = self.skill_level * 25
            return base_value + hp_bonus
        
        return base_value
```

#### Command Pattern для изучения навыков
```python
# src/progression/skill_commands.py
class SkillCommand(ABC):
    """Команда для операций с навыками"""
    
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        pass

class LearnSkillCommand(SkillCommand):
    """Команда изучения навыка"""
    def __init__(self, entity: Entity, skill_id: str):
        self.entity = entity
        self.skill_id = skill_id
        self.skill_points_spent = 1
    
    def execute(self) -> bool:
        exp_comp = self.entity.get_component(ExperienceComponent)
        skill_tree_comp = self.entity.get_component(SkillTreeComponent)
        
        if exp_comp.available_skill_points >= self.skill_points_spent:
            # Проверка пререквизитов
            if self._check_prerequisites():
                # Изучение навыка
                skill = skill_tree_comp.learned_skills.get(self.skill_id)
                if not skill:
                    skill = SkillComponent(self.skill_id, self._get_skill_branch())
                    skill_tree_comp.learned_skills[self.skill_id] = skill
                
                skill.current_level += 1
                exp_comp.available_skill_points -= self.skill_points_spent
                
                # Применение эффекта навыка
                strategy = self._get_skill_strategy(self.skill_id)
                strategy.apply_skill_effect(self.entity, skill.current_level)
                
                return True
        
        return False
    
    def undo(self) -> bool:
        # Откат изучения навыка (для системы переспециализации)
        exp_comp = self.entity.get_component(ExperienceComponent)
        skill_tree_comp = self.entity.get_component(SkillTreeComponent)
        
        skill = skill_tree_comp.learned_skills.get(self.skill_id)
        if skill and skill.current_level > 0:
            # Удаление эффекта навыка
            strategy = self._get_skill_strategy(self.skill_id)
            strategy.remove_skill_effect(self.entity, skill.current_level)
            
            skill.current_level -= 1
            exp_comp.available_skill_points += self.skill_points_spent
            
            return True
        
        return False

class RespecSkillsCommand(SkillCommand):
    """Команда сброса всех навыков"""
    def __init__(self, entity: Entity, cost: int):
        self.entity = entity
        self.cost = cost
        self.backup_skills = {}
    
    def execute(self) -> bool:
        # Сохранение текущего состояния для отката
        skill_tree_comp = self.entity.get_component(SkillTreeComponent)
        self.backup_skills = deepcopy(skill_tree_comp.learned_skills)
        
        # Сброс всех навыков
        total_points = 0
        for skill in skill_tree_comp.learned_skills.values():
            total_points += skill.current_level
            # Удаление эффектов навыков
            strategy = self._get_skill_strategy(skill.skill_id)
            strategy.remove_skill_effect(self.entity, skill.current_level)
        
        # Очистка изученных навыков
        skill_tree_comp.learned_skills.clear()
        
        # Возврат очков навыков
        exp_comp = self.entity.get_component(ExperienceComponent)
        exp_comp.available_skill_points += total_points
        
        return True
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── progression_components.py # Компоненты прогрессии
├── progression/
│   ├── skill_strategies.py       # Стратегии навыков (Strategy Pattern)
│   ├── skill_decorators.py       # Декораторы бонусов (Decorator Pattern)
│   ├── skill_commands.py         # Команды навыков (Command Pattern)
│   ├── experience_system.py      # Система опыта (ECS System + Observer)
│   ├── skill_tree_system.py      # Система дерева навыков (ECS System)
│   └── progression_manager.py    # Управление прогрессией
├── ui/
│   ├── skill_tree_ui.py          # Интерфейс дерева навыков
│   ├── level_up_notification.py  # Уведомления о повышении уровня
│   └── experience_bar.py         # Полоска опыта
└── events/
    └── progression_events.py     # События прогрессии
```

### Файлы для создания/изменения
- `src/core/ecs/progression_components.py` - компоненты прогрессии
- `src/progression/skill_strategies.py` - стратегии навыков (Strategy Pattern)
- `src/progression/skill_decorators.py` - декораторы бонусов (Decorator Pattern)
- `src/progression/skill_commands.py` - команды навыков (Command Pattern)
- `src/progression/experience_system.py` - система опыта (ECS System + Observer)
- `src/progression/skill_tree_system.py` - система дерева навыков (ECS System)
- `src/events/progression_events.py` - события прогрессии
- `src/ui/skill_tree_ui.py` - интерфейс дерева навыков
- `src/ui/level_up_notification.py` - уведомления о повышении уровня
- `src/entities/player.py` - интеграция с игроком

### Структура системы навыков
```python
class Skill:
    def __init__(self, name, max_level, effects):
        self.name = name
        self.current_level = 0
        self.max_level = max_level
        self.effects = effects  # список эффектов по уровням
        
class SkillTree:
    def __init__(self):
        self.branches = {
            'magic': MagicBranch(),
            'melee': MeleeBranch(),
            'ranged': RangedBranch(),
            'vitality': VitalityBranch()
        }
        self.available_points = 0
```

### Конфигурация
```ini
[PROGRESSION]
base_xp_per_level = 100
xp_multiplier = 1.2
max_level = 50
skill_points_per_level = 1

[XP_REWARDS]
enemy_kill_base = 10
quest_completion_base = 50
area_discovery = 25
item_first_use = 5
```

### Интеграция с существующими системами
- [ ] **Боевая система**: применение бонусов к урону и скорости
- [ ] **Магическая система**: увеличение маны и эффективности
- [ ] **Система здоровья**: увеличение HP и регенерация
- [ ] **Система сохранений**: сохранение прогресса навыков
- [ ] **UI система**: отображение доступных очков и прогресса

### Интерфейс дерева навыков
- [ ] **Открытие**: клавиша C (Character)
- [ ] **Визуализация**:
  - [ ] 4 ветки в виде древовидной структуры
  - [ ] Иконки навыков с индикацией уровня
  - [ ] Линии связи между навыками
  - [ ] Подсветка доступных для изучения навыков
- [ ] **Взаимодействие**:
  - [ ] Клик для вложения очка навыка
  - [ ] Подтверждение выбора
  - [ ] Предпросмотр эффектов
  - [ ] Возможность сброса навыков (за плату)

## Критерии готовности
- [ ] Игрок получает опыт за различные действия
- [ ] Система уровней работает корректно
- [ ] Все 12 навыков (4x3) реализованы и функциональны
- [ ] Интерфейс дерева навыков интуитивно понятен
- [ ] Бонусы от навыков корректно применяются
- [ ] Система сохраняет прогресс навыков
- [ ] Балансировка не делает игру слишком легкой/сложной

## Приоритет
**Средний** - Важно для долгосрочной мотивации

## Зависимости
- Issue #03 (Система магии) - для ветки магии
- Issue #04 (Оружие) - для веток ближнего/дальнего боя
- Issue #05 (Враги) - для получения опыта
- Текущая система здоровья

## Балансировка
- Каждый уровень должен ощущаться как достижение
- Навыки должны значительно влиять на стиль игры
- Максимальный уровень должен достигаться за 20-30 часов игры
- Различные ветки должны быть одинаково привлекательными

## Расширения (будущие версии)
- [ ] **Престиж система**: сброс уровня для дополнительных бонусов
- [ ] **Специализации**: уникальные комбинации навыков
- [ ] **Мастерские навыки**: особые способности на высоких уровнях
- [ ] **Синергии**: бонусы за изучение навыков из разных веток

## Примерное время реализации
3-4 недели

## Связанные issues
- #03 (Система магии) - ветка магии
- #04 (Оружие) - ветки боя
- #05 (Враги) - источник опыта
- #09 (Квесты) - источник опыта

---

## Подзадачи для реализации

### 📈 Фаза 1: Базовая система опыта и уровней
**Цель**: Создание основ системы прогрессии персонажа

#### 1.1 ECS компоненты прогрессии
- [ ] Создать `src/core/ecs/progression_components.py` - ExperienceComponent, SkillTreeComponent
- [ ] Создать SkillComponent, StatModifierComponent
- [ ] Создать `test_progression_components.py` - unit тесты компонентов прогрессии
- [ ] Все компоненты прогрессии работают с базовой функциональностью

#### 1.2 Система опыта как Observer
- [ ] Создать `src/progression/experience_system.py` - ExperienceSystem (ECS System + Observer)
- [ ] Подписка на события убийства врагов, выполнения квестов, исследований
- [ ] Создать `test_experience_system.py` - тестирование получения опыта
- [ ] Игрок корректно получает опыт за различные действия

#### 1.3 UI системы опыта
- [ ] Создать `src/ui/experience_bar.py` - полоска опыта в интерфейсе
- [ ] Создать `src/ui/level_up_notification.py` - уведомления о повышении уровня
- [ ] Создать `test_experience_ui.py` - тестирование UI опыта
- [ ] Полоска опыта и уведомления корректно отображаются

### 🌳 Фаза 2: Система дерева навыков
**Цель**: Создание 4 веток навыков с 3 навыками каждая

#### 2.1 Strategy Pattern для навыков
- [ ] Создать `src/progression/skill_strategies.py` - SkillStrategy, PassiveSkillStrategy, ActiveSkillStrategy
- [ ] Создать MagicSkillStrategy, MeleeSkillStrategy, RangedSkillStrategy, VitalitySkillStrategy
- [ ] Создать `test_skill_strategies.py` - тестирование стратегий навыков
- [ ] Каждая ветка навыков имеет уникальные эффекты

#### 2.2 Command Pattern для изучения навыков
- [ ] Создать `src/progression/skill_commands.py` - SkillCommand, LearnSkillCommand
- [ ] Создать RespecSkillsCommand для сброса навыков
- [ ] Создать `test_skill_commands.py` - тестирование команд навыков
- [ ] Игрок может изучать и сбрасывать навыки

#### 2.3 Система дерева навыков как ECS System
- [ ] Создать `src/progression/skill_tree_system.py` - SkillTreeSystem (ECS System)
- [ ] Интеграция с системой очков навыков
- [ ] Создать `test_skill_tree_system.py` - тестирование системы навыков
- [ ] Система навыков корректно применяет эффекты

### 🔮 Фаза 3: Ветка магических навыков
**Цель**: Реализация 3 навыков магии

#### 3.1 Навык "Увеличение маны"
- [ ] Реализовать ManaBoostSkill - увеличение максимальной маны на 20/40/60
- [ ] Интеграция с MagicComponent
- [ ] Создать `test_mana_boost_skill.py` - тестирование навыка маны
- [ ] Навык корректно увеличивает максимальную ману

#### 3.2 Навык "Усиление магического урона"
- [ ] Реализовать MagicDamageSkill - +25%/50%/75% урон заклинаний
- [ ] Интеграция с системой заклинаний
- [ ] Создать `test_magic_damage_skill.py` - тестирование навыка урона
- [ ] Навык корректно усиливает магические атаки

#### 3.3 Навык "Продление действия заклинаний"
- [ ] Реализовать SpellDurationSkill - +50%/100%/150% длительность эффектов
- [ ] Интеграция с системой статусных эффектов
- [ ] Создать `test_spell_duration_skill.py` - тестирование продления эффектов
- [ ] Навык корректно продлевает действие заклинаний

### ⚔️ Фаза 4: Ветка ближнего боя
**Цель**: Реализация 3 навыков ближнего боя

#### 4.1 Навык "Увеличение урона ближнего оружия"
- [ ] Реализовать MeleeDamageSkill - +20%/40%/60% урон мечей
- [ ] Интеграция с WeaponComponent
- [ ] Создать `test_melee_damage_skill.py` - тестирование навыка урона ближнего боя
- [ ] Навык корректно усиливает урон мечей

#### 4.2 Навык "Скорость атак"
- [ ] Реализовать AttackSpeedSkill - +15%/30%/45% скорость атаки
- [ ] Интеграция с системой атаки
- [ ] Создать `test_attack_speed_skill.py` - тестирование скорости атак
- [ ] Навык корректно увеличивает скорость атаки

#### 4.3 Навык "Критический урон"
- [ ] Реализовать CriticalHitSkill - 5%/10%/15% шанс крита + 50%/75%/100% урон
- [ ] Интеграция с системой боя
- [ ] Создать `test_critical_hit_skill.py` - тестирование критических ударов
- [ ] Навык корректно добавляет критические удары

### 🏹 Фаза 5: Ветки дальнего боя и выносливости
**Цель**: Завершение всех 4 веток навыков

#### 5.1 Ветка дальнего боя (3 навыка)
- [ ] Реализовать RangedDamageSkill - +25%/50%/75% урон луков/арбалетов
- [ ] Реализовать RangedAccuracySkill - +20%/40%/60% дальность, меньше разброса
- [ ] Реализовать ReloadSpeedSkill - +20%/40%/60% скорость перезарядки
- [ ] Создать `test_ranged_skills.py` - тестирование навыков дальнего боя
- [ ] Все навыки дальнего боя работают корректно

#### 5.2 Ветка выносливости (3 навыка)
- [ ] Реализовать HealthBoostSkill - +25/50/75 максимального HP
- [ ] Реализовать HealthRegenSkill - регенерация 1 HP каждые 10/5/3 секунды
- [ ] Реализовать DebuffResistanceSkill - -25%/50%/75% длительность дебафов
- [ ] Создать `test_vitality_skills.py` - тестирование навыков выносливости
- [ ] Все навыки выносливости работают корректно

#### 5.3 Интеграция всех веток навыков
- [ ] Проверка совместимости всех веток навыков
- [ ] Создать `test_all_skills_integration.py` - интеграционные тесты всех навыков
- [ ] Все 12 навыков работают без конфликтов

### 🎮 Фаза 6: Пользовательский интерфейс навыков
**Цель**: UI для управления навыками и их визуализация

#### 6.1 Интерфейс дерева навыков
- [ ] Создать `src/ui/skill_tree_ui.py` - окно дерева навыков (клавиша C)
- [ ] Визуализация 4 веток с иконками и связями
- [ ] Создать `test_skill_tree_ui.py` - тестирование UI дерева навыков
- [ ] Удобный интерфейс для изучения навыков

#### 6.2 Трекер навыков в игре
- [ ] Создать `src/ui/skill_tracker_ui.py` - отображение активных эффектов навыков
- [ ] Показ доступных очков навыков в HUD
- [ ] Создать `test_skill_tracker.py` - тестирование трекера навыков
- [ ] Игрок видит активные эффекты и доступные очки

#### 6.3 Система подсказок навыков
- [ ] Создать всплывающие подсказки для каждого навыка
- [ ] Предпросмотр эффектов перед изучением
- [ ] Создать `test_skill_tooltips.py` - тестирование подсказок
- [ ] Подсказки показывают полную информацию о навыках

### 🔧 Фаза 7: Интеграция и балансировка
**Цель**: Финальная интеграция со всеми системами

#### 7.1 Decorator Pattern для бонусов навыков
- [ ] Создать `src/progression/skill_decorators.py` - SkillBonusDecorator, WeaponSkillDecorator
- [ ] Создать MagicSkillDecorator, HealthSkillDecorator
- [ ] Создать `test_skill_decorators.py` - тестирование декораторов навыков
- [ ] Бонусы навыков корректно применяются к характеристикам

#### 7.2 События прогрессии
- [ ] Создать `src/events/progression_events.py` - ExperienceGainedEvent, LevelUpEvent, SkillLearnedEvent
- [ ] Интеграция с системой уведомлений
- [ ] Создать `test_progression_events.py` - тестирование событий прогрессии
- [ ] События прогрессии корректно обрабатываются системой

#### 7.3 Балансировка и конфигурация
- [ ] Добавить настройки прогрессии в `config.ini` - опыт за уровень, эффекты навыков
- [ ] Создать `test_progression_balance.py` - тесты игрового баланса
- [ ] Создать документацию по системе навыков в `CLAUDE.md`
- [ ] Система прогрессии сбалансирована для 20-30 часов игры

---

## 🌳 Дерево зависимостей подзадач

```
Фаза 1: Базовая система опыта
├── 1.1 ECS компоненты прогрессии
├── 1.2 Система опыта Observer (зависит от 1.1)
└── 1.3 UI системы опыта (зависит от 1.2)

Фаза 2: Система дерева навыков
├── 2.1 Strategy Pattern для навыков (зависит от 1.1)
├── 2.2 Command Pattern навыков (зависит от 2.1)
└── 2.3 Система дерева навыков (зависит от 2.1, 2.2)

Фаза 3: Ветка магических навыков
├── 3.1 Навык маны (зависит от 2.3, Issue #03)
├── 3.2 Навык магического урона (зависит от 3.1, Issue #03)
└── 3.3 Навык продления эффектов (зависит от 3.2, Issue #03)

Фаза 4: Ветка ближнего боя
├── 4.1 Навык урона ближнего боя (зависит от 2.3, Issue #04)
├── 4.2 Навык скорости атак (зависит от 4.1, Issue #04)
└── 4.3 Навык критических ударов (зависит от 4.2)

Фаза 5: Завершающие ветки навыков (может выполняться параллельно после Фазы 2)
├── 5.1 Ветка дальнего боя (зависит от 2.3, Issue #04)
├── 5.2 Ветка выносливости (зависит от 2.3)
└── 5.3 Интеграция веток (зависит от 5.1, 5.2, 3.3, 4.3)

Фаза 6: UI навыков
├── 6.1 Интерфейс дерева навыков (зависит от 5.3)
├── 6.2 Трекер навыков (зависит от 6.1)
└── 6.3 Система подсказок (зависит от 6.1)

Фаза 7: Интеграция и балансировка
├── 7.1 Decorator Pattern (зависит от 5.3)
├── 7.2 События прогрессии (зависит от 1.2, 6.1)
└── 7.3 Балансировка (зависит от всех предыдущих фаз)
```

**Критический путь**: 1.1 → 1.2 → 2.1 → 2.2 → 2.3 → 5.3 → 6.1 → 7.3

**Минимальные требования к тестированию**: 
- Unit тесты для каждого навыка и компонента прогрессии
- Интеграционные тесты для взаимодействия с боевыми системами
- Тесты балансировки для проверки прогрессии персонажа
- Минимальное покрытие: 90% для системы навыков и прогрессии