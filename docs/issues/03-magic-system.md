# Issue #03: Система магии и стихий

## Описание
Реализация полноценной системы магии с тремя стихиями (Огонь, Холод, Молния), системой маны и возможностью комбинирования заклинаний.

## Цель
Добавить магическую боевую систему как альтернативу физическим атакам, с уникальными эффектами и тактическими возможностями.

## Требования

### Система маны
- [ ] Добавление маны к характеристикам игрока
- [ ] Максимальная мана: 100 MP (улучшается навыками)
- [ ] Регенерация маны со временем
- [ ] Полоска маны в UI (сине-фиолетовый градиент)
- [ ] Стоимость заклинаний в мане

### Магические стихии
- [ ] **Огонь**:
  - [ ] Базовый урон + дебаф горения
  - [ ] Эффективен против холода
  - [ ] Визуальные эффекты: красно-оранжевые частицы
- [ ] **Холод**:
  - [ ] Базовый урон + замедление врагов
  - [ ] Эффективен против огня
  - [ ] Визуальные эффекты: сине-белые кристаллы
- [ ] **Молния**:
  - [ ] Высокий урон + возможность цепной реакции
  - [ ] Мгновенное попадание
  - [ ] Визуальные эффекты: желто-фиолетовые разряды

### Типы магических атак
- [ ] **Дальний урон**:
  - [ ] Магические снаряды
  - [ ] Лучи и молнии
  - [ ] Дальность: больше физических атак
- [ ] **Ближний урон**:
  - [ ] Магические взрывы вокруг игрока
  - [ ] Усиление оружия стихиями
  - [ ] Защитные ауры

### Система комбинирования
- [ ] **Две руки - два заклинания**:
  - [ ] Каждая рука может содержать заклинание одной стихии
  - [ ] Независимое использование каждой руки
- [ ] **Комбо-эффекты**:
  - [ ] Огонь + Холод = Паровой взрыв (супер урон)
  - [ ] Огонь + Молния = Плазменный разряд
  - [ ] Холод + Молния = Ледяная буря
- [ ] **Супермаг режим**:
  - [ ] Одновременное использование обеих рук
  - [ ] Повышенная стоимость маны
  - [ ] Усиленные эффекты

## Технические детали

### Архитектурные паттерны

#### ECS Components для магической системы
```python
# src/core/ecs/magic_components.py
class MagicComponent(Component):
    """Компонент магических способностей"""
    def __init__(self, max_mana: int = 100):
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.mana_regen_rate = 1.0
        self.known_spells = set()
        self.active_effects = []

class SpellComponent(Component):
    """Компонент заклинания"""
    def __init__(self, spell_id: str, element: str, mana_cost: int):
        self.spell_id = spell_id
        self.element = element  # fire, cold, lightning
        self.mana_cost = mana_cost
        self.cooldown = 0
        self.damage = 0
        self.range = 0
        self.duration = 0

class ElementalResistanceComponent(Component):
    """Компонент сопротивлений к стихиям"""
    def __init__(self):
        self.resistances = {
            'fire': 0.0,     # 0.0 = нет сопротивления, 0.5 = 50% сопротивления
            'cold': 0.0,
            'lightning': 0.0
        }

class HandSlotComponent(Component):
    """Компонент слотов рук для заклинаний"""
    def __init__(self):
        self.left_hand = None   # SpellComponent или WeaponComponent
        self.right_hand = None
        self.can_dual_cast = True
```

#### Strategy Pattern для различных типов магии
```python
# src/magic/spell_strategies.py
class SpellStrategy(ABC):
    """Стратегия применения заклинания"""
    
    @abstractmethod
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        pass
    
    @abstractmethod
    def calculate_damage(self, caster: Entity, target: Entity) -> float:
        pass

class ProjectileSpellStrategy(SpellStrategy):
    """Стратегия для снарядных заклинаний (огненный шар, ледяная стрела)"""
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        spell_comp = caster.get_component(SpellComponent)
        magic_comp = caster.get_component(MagicComponent)
        
        if magic_comp.current_mana >= spell_comp.mana_cost:
            # Создаем снаряд
            projectile = self._create_projectile(caster, target_pos, spell_comp)
            world.add_entity(projectile)
            magic_comp.current_mana -= spell_comp.mana_cost
            return True
        return False

class InstantSpellStrategy(SpellStrategy):
    """Стратегия для мгновенных заклинаний (удар молнии)"""
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        # Мгновенное попадание без снаряда
        targets = self._find_targets_in_line(caster, target_pos, world)
        for target in targets:
            damage = self.calculate_damage(caster, target)
            self._apply_damage(target, damage)
        return True

class AuraSpellStrategy(SpellStrategy):
    """Стратегия для аурных заклинаний (щиты, усиления)"""
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        # Создаем временный эффект на кастере
        aura_effect = self._create_aura_effect(caster)
        magic_comp = caster.get_component(MagicComponent)
        magic_comp.active_effects.append(aura_effect)
        return True

class ComboSpellStrategy(SpellStrategy):
    """Стратегия для комбинированных заклинаний"""
    def __init__(self, left_strategy: SpellStrategy, right_strategy: SpellStrategy):
        self.left_strategy = left_strategy
        self.right_strategy = right_strategy
        self.combo_effects = {
            ('fire', 'cold'): 'steam_explosion',
            ('fire', 'lightning'): 'plasma_burst',
            ('cold', 'lightning'): 'ice_storm'
        }
    
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        # Одновременное применение двух заклинаний с комбо-эффектом
        left_element = self._get_element(self.left_strategy)
        right_element = self._get_element(self.right_strategy)
        
        combo_type = self.combo_effects.get((left_element, right_element))
        if combo_type:
            return self._cast_combo_spell(caster, target_pos, world, combo_type)
        else:
            # Обычное двойное применение
            return (self.left_strategy.cast(caster, target_pos, world) and
                   self.right_strategy.cast(caster, target_pos, world))
```

#### Decorator Pattern для модификации заклинаний
```python
# src/magic/spell_decorators.py
class SpellModifier(ABC):
    """Декоратор для модификации заклинаний"""
    def __init__(self, spell_strategy: SpellStrategy):
        self._spell_strategy = spell_strategy
    
    @abstractmethod
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        pass

class PowerfulSpellModifier(SpellModifier):
    """Модификатор увеличения силы заклинания"""
    def __init__(self, spell_strategy: SpellStrategy, power_multiplier: float):
        super().__init__(spell_strategy)
        self.power_multiplier = power_multiplier
    
    def cast(self, caster: Entity, target_pos: tuple, world: World) -> bool:
        # Временно увеличиваем силу заклинания
        original_damage = self._get_spell_damage(caster)
        self._set_spell_damage(caster, original_damage * self.power_multiplier)
        
        result = self._spell_strategy.cast(caster, target_pos, world)
        
        # Восстанавливаем оригинальную силу
        self._set_spell_damage(caster, original_damage)
        return result

class ExtendedRangeModifier(SpellModifier):
    """Модификатор увеличения дальности"""
    def __init__(self, spell_strategy: SpellStrategy, range_multiplier: float):
        super().__init__(spell_strategy)
        self.range_multiplier = range_multiplier

class ManaCostReductionModifier(SpellModifier):
    """Модификатор снижения стоимости маны"""
    def __init__(self, spell_strategy: SpellStrategy, cost_reduction: float):
        super().__init__(spell_strategy)
        self.cost_reduction = cost_reduction  # 0.2 = 20% снижение
```

#### Observer Pattern для магических событий
```python
# src/events/magic_events.py
class SpellCastEvent(GameEvent):
    """Событие применения заклинания"""
    def __init__(self, caster: Entity, spell: SpellComponent, target_pos: tuple):
        super().__init__("spell_cast")
        self.caster = caster
        self.spell = spell
        self.target_pos = target_pos

class ManaChangedEvent(GameEvent):
    """Событие изменения маны"""
    def __init__(self, entity: Entity, old_mana: int, new_mana: int):
        super().__init__("mana_changed")
        self.entity = entity
        self.old_mana = old_mana
        self.new_mana = new_mana

class ComboSpellEvent(GameEvent):
    """Событие комбинированного заклинания"""
    def __init__(self, caster: Entity, combo_type: str, elements: tuple):
        super().__init__("combo_spell")
        self.caster = caster
        self.combo_type = combo_type
        self.elements = elements

# Использование в системах
class MagicSystem(System):
    def __init__(self, event_system: EventSystem):
        self.event_system = event_system
        self.event_system.subscribe("spell_cast", self.handle_spell_cast)
        self.event_system.subscribe("combo_spell", self.handle_combo_spell)
    
    def handle_spell_cast(self, event: SpellCastEvent):
        # Обновление статистики, проверка квестов, прокачка навыков
        self._update_magic_skill(event.caster, event.spell.element)
        self._check_spell_achievements(event.caster, event.spell)
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── magic_components.py       # Компоненты магической системы
├── magic/
│   ├── spell_strategies.py       # Стратегии применения заклинаний
│   ├── spell_decorators.py       # Декораторы модификации заклинаний
│   ├── magic_system.py           # Основная система магии (ECS System)
│   ├── element_system.py         # Система взаимодействия стихий
│   └── mana_system.py            # Система управления маной (ECS System)
├── effects/
│   ├── spell_effects.py          # Визуальные эффекты заклинаний
│   └── particle_system.py        # Система частиц для магии
└── events/
    └── magic_events.py           # События магической системы
```

### Файлы для создания/изменения
- `src/core/ecs/magic_components.py` - компоненты магической системы
- `src/magic/spell_strategies.py` - стратегии применения заклинаний
- `src/magic/spell_decorators.py` - декораторы модификации заклинаний
- `src/magic/magic_system.py` - основная система магии (ECS System)
- `src/magic/mana_system.py` - система управления маной (ECS System)
- `src/effects/spell_effects.py` - визуальные эффекты заклинаний
- `src/events/magic_events.py` - события магической системы
- `src/entities/player.py` - добавление магических компонентов
- `src/ui/mana_bar.py` - полоска маны в интерфейсе

### Классы заклинаний
```python
# Примерная структура
class Spell:
    def __init__(self, element, mana_cost, damage, range, cooldown):
        pass

class FireBolt(Spell):
    # Огненный снаряд
    pass

class IceShield(Spell):
    # Ледяной щит
    pass

class LightningStrike(Spell):
    # Удар молнии
    pass
```

### Конфигурация
```ini
[MAGIC]
max_mana = 100
mana_regen_rate = 1.0
spell_cooldown_base = 500

[SPELLS]
fire_bolt_cost = 15
ice_shield_cost = 20
lightning_strike_cost = 25
combo_multiplier = 1.5
```

### Интеграция с существующими системами
- Расширение боевой системы для магических атак
- Обновление системы управления (клавиши для заклинаний)
- Интеграция с системой статистики (использованные заклинания)
- Расширение системы сохранений (изученные заклинания, мана)

## Критерии готовности
- [ ] Игрок может использовать все 3 стихии
- [ ] Мана корректно тратится и восстанавливается
- [ ] Комбо-эффекты работают при одновременном использовании
- [ ] Визуальные эффекты отображаются корректно
- [ ] Система сбалансирована (не слишком сильная/слабая)
- [ ] Интеграция с UI работает без ошибок

## Приоритет
**Высокий** - Ключевая игровая механика

## Зависимости
- Текущая боевая система
- Система управления
- UI система

## Балансировка
- Стоимость заклинаний должна требовать тактического планирования
- Комбо-эффекты должны быть мощными, но дорогими
- Регенерация маны не должна быть слишком быстрой
- Кулдауны должны предотвращать спам заклинаний

## Примерное время реализации
2-3 недели

## Связанные issues
- #04 (Расширенное оружие) - интеграция магии с оружием
- #06 (Дерево навыков) - ветка магии
- #08 (Инвентарь) - магические предметы и зелья маны