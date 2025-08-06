# Issue #04: Расширенная система оружия и защиты

## Описание
Реализация разнообразного оружия (мечи, арбалеты, магические посохи) и системы защиты (физические и магические щиты).

## Цель
Расширить боевую систему, добавив различные типы оружия с уникальными характеристиками и систему защиты для тактического разнообразия.

## Требования

### Система оружия
- [ ] **Мечи (ближний бой)**:
  - [ ] Короткий меч: быстрые атаки, низкий урон
  - [ ] Длинный меч: средние характеристики
  - [ ] Двуручный меч: медленные атаки, высокий урон
- [ ] **Дальнобойное оружие**:
  - [ ] Арбалет: высокий урон, медленная перезарядка
  - [ ] Лук: средний урон, быстрая стрельба
  - [ ] Метательные ножи: низкий урон, очень быстрые
- [ ] **Магическое оружие**:
  - [ ] Посохи стихий (огонь, холод, молния)
  - [ ] Зачарованные мечи с элементальным уроном
  - [ ] Артефактное оружие с уникальными способностями

### Система рук и экипировки
- [ ] **Одноручное оружие**:
  - [ ] Меч в одной руке, щит в другой
  - [ ] Меч в одной руке, заклинание в другой
- [ ] **Двуручное оружие**:
  - [ ] Двуручные мечи, арбалеты
  - [ ] Блокирует использование щитов
- [ ] **Двойное оружие**:
  - [ ] Два меча одновременно
  - [ ] Увеличенная скорость атак
  - [ ] Комбо-атаки

### Система защиты
- [ ] **Физические щиты**:
  - [ ] Деревянный щит: базовая защита
  - [ ] Металлический щит: высокая защита
  - [ ] Магический щит: защита от заклинаний
- [ ] **Магические щиты**:
  - [ ] Временные заклинания защиты (5 минут)
  - [ ] Полная блокировка определенных типов урона
  - [ ] Стоимость в мане для поддержания
- [ ] **Механика блокирования**:
  - [ ] Активная блокировка (удержание клавиши)
  - [ ] Направленная блокировка (по направлению взгляда)
  - [ ] Идеальная блокировка (тайминг)

## Технические детали

### Архитектурные паттерны

#### ECS Components для системы оружия
```python
# src/core/ecs/combat_components.py
class WeaponComponent(Component):
    """Компонент оружия"""
    def __init__(self, weapon_type: str, damage: int, attack_speed: float):
        self.weapon_type = weapon_type  # SWORD, BOW, CROSSBOW, STAFF
        self.base_damage = damage
        self.attack_speed = attack_speed
        self.range = 0
        self.critical_chance = 0.0
        self.enchantments = []
        self.sockets = []  # для камней и рун

class ShieldComponent(Component):
    """Компонент щита"""
    def __init__(self, shield_type: str, block_value: int):
        self.shield_type = shield_type  # WOODEN, METAL, MAGIC
        self.block_value = block_value
        self.durability = 100
        self.resistances = {}
        self.active_block = False

class EquipmentComponent(Component):
    """Компонент экипировки"""
    def __init__(self):
        self.main_hand = None      # WeaponComponent
        self.off_hand = None       # WeaponComponent или ShieldComponent
        self.is_dual_wielding = False
        self.is_two_handed = False

class EnchantmentComponent(Component):
    """Компонент зачарований"""
    def __init__(self, enchantment_type: str, power: int, duration: int = -1):
        self.enchantment_type = enchantment_type  # FIRE, COLD, LIGHTNING, SHARPNESS
        self.power = power
        self.duration = duration  # -1 для постоянных зачарований
        self.remaining_time = duration
```

#### Strategy Pattern для различных типов оружия
```python
# src/combat/weapon_strategies.py
class WeaponStrategy(ABC):
    """Стратегия использования оружия"""
    
    @abstractmethod
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        pass
    
    @abstractmethod
    def calculate_damage(self, attacker: Entity, weapon: WeaponComponent) -> float:
        pass

class MeleeWeaponStrategy(WeaponStrategy):
    """Стратегия ближнего боя"""
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        weapon_comp = attacker.get_component(WeaponComponent)
        
        # Проверка дальности
        if not self._in_melee_range(attacker, target):
            return AttackResult(False, "Target out of range")
        
        damage = self.calculate_damage(attacker, weapon_comp)
        
        # Проверка критического удара
        if self._is_critical_hit(weapon_comp):
            damage *= 2.0
            return AttackResult(True, "Critical hit!", damage, is_critical=True)
        
        return AttackResult(True, "Hit", damage)

class RangedWeaponStrategy(WeaponStrategy):
    """Стратегия дальнего боя"""
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        weapon_comp = attacker.get_component(WeaponComponent)
        
        # Создаем снаряд
        projectile = self._create_projectile(attacker, target, weapon_comp)
        world.add_entity(projectile)
        
        # Проверяем наличие боеприпасов
        ammo_comp = attacker.get_component(AmmoComponent)
        if ammo_comp and ammo_comp.count > 0:
            ammo_comp.count -= 1
            return AttackResult(True, "Shot fired", 0)  # урон будет при попадании
        
        return AttackResult(False, "No ammo")

class DualWieldStrategy(WeaponStrategy):
    """Стратегия двойного оружия"""
    def __init__(self, main_hand_strategy: WeaponStrategy, off_hand_strategy: WeaponStrategy):
        self.main_hand_strategy = main_hand_strategy
        self.off_hand_strategy = off_hand_strategy
    
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        # Атака двумя руками с небольшой задержкой
        main_result = self.main_hand_strategy.attack(attacker, target, world)
        
        # Вторая атака с 50% урона
        off_result = self.off_hand_strategy.attack(attacker, target, world)
        if off_result.success:
            off_result.damage *= 0.5
        
        return AttackResult.combine(main_result, off_result)

class MagicWeaponStrategy(WeaponStrategy):
    """Стратегия магического оружия (посохи)"""
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        weapon_comp = attacker.get_component(WeaponComponent)
        magic_comp = attacker.get_component(MagicComponent)
        
        # Посох усиливает магические атаки
        spell_power_bonus = weapon_comp.base_damage * 0.1
        
        # Применяем заклинание с бонусом от посоха
        return self._cast_weapon_spell(attacker, target, world, spell_power_bonus)
```

#### Decorator Pattern для улучшений оружия
```python
# src/combat/weapon_decorators.py
class WeaponModifier(ABC):
    """Декоратор для модификации оружия"""
    def __init__(self, weapon_strategy: WeaponStrategy):
        self._weapon_strategy = weapon_strategy
    
    @abstractmethod
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        pass

class EnchantedWeaponModifier(WeaponModifier):
    """Модификатор зачарованного оружия"""
    def __init__(self, weapon_strategy: WeaponStrategy, enchantment: EnchantmentComponent):
        super().__init__(weapon_strategy)
        self.enchantment = enchantment
    
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        result = self._weapon_strategy.attack(attacker, target, world)
        
        if result.success:
            # Добавляем элементальный урон
            elemental_damage = self._calculate_elemental_damage(self.enchantment)
            result.damage += elemental_damage
            result.effects.append(f"{self.enchantment.enchantment_type} damage")
        
        return result

class SharpnessModifier(WeaponModifier):
    """Модификатор заточки оружия (+1, +2, +3...)"""
    def __init__(self, weapon_strategy: WeaponStrategy, sharpness_level: int):
        super().__init__(weapon_strategy)
        self.sharpness_level = sharpness_level
    
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        result = self._weapon_strategy.attack(attacker, target, world)
        
        if result.success:
            # Увеличиваем урон на основе уровня заточки
            bonus_damage = result.damage * (self.sharpness_level * 0.1)
            result.damage += bonus_damage
        
        return result

class SocketedWeaponModifier(WeaponModifier):
    """Модификатор оружия с камнями в гнездах"""
    def __init__(self, weapon_strategy: WeaponStrategy, gems: List[GemComponent]):
        super().__init__(weapon_strategy)
        self.gems = gems
    
    def attack(self, attacker: Entity, target: Entity, world: World) -> AttackResult:
        result = self._weapon_strategy.attack(attacker, target, world)
        
        if result.success:
            for gem in self.gems:
                # Каждый камень добавляет свой эффект
                gem_effect = self._apply_gem_effect(gem, result)
                result = gem_effect
        
        return result
```

#### State Pattern для блокирования щитом
```python
# src/combat/shield_states.py
class ShieldState(ABC):
    """Состояние щита"""
    
    @abstractmethod
    def handle_attack(self, defender: Entity, attack: AttackResult) -> AttackResult:
        pass

class PassiveShieldState(ShieldState):
    """Пассивное состояние щита"""
    def handle_attack(self, defender: Entity, attack: AttackResult) -> AttackResult:
        # Щит не активен, атака проходит полностью
        return attack

class ActiveBlockState(ShieldState):
    """Активная блокировка"""
    def handle_attack(self, defender: Entity, attack: AttackResult) -> AttackResult:
        shield_comp = defender.get_component(ShieldComponent)
        
        if shield_comp and shield_comp.active_block:
            # Вычисляем заблокированный урон
            blocked_damage = min(attack.damage, shield_comp.block_value)
            remaining_damage = max(0, attack.damage - blocked_damage)
            
            # Снижаем прочность щита
            shield_comp.durability -= 1
            
            return AttackResult(True, "Blocked", remaining_damage, 
                              blocked_damage=blocked_damage)
        
        return attack

class PerfectBlockState(ShieldState):
    """Идеальная блокировка (по таймингу)"""
    def handle_attack(self, defender: Entity, attack: AttackResult) -> AttackResult:
        # Полная блокировка + контратака
        return AttackResult(False, "Perfect block!", 0, 
                          counter_attack=True)

class ShieldSystem(System):
    """Система управления щитами"""
    def __init__(self):
        self.states = {
            'passive': PassiveShieldState(),
            'active': ActiveBlockState(),
            'perfect': PerfectBlockState()
        }
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── combat_components.py      # Компоненты боевой системы
├── combat/
│   ├── weapon_strategies.py      # Стратегии использования оружия
│   ├── weapon_decorators.py      # Декораторы улучшений оружия
│   ├── shield_states.py          # Состояния щитов
│   ├── weapon_system.py          # Система оружия (ECS System)
│   ├── shield_system.py          # Система щитов (ECS System)
│   └── combat_manager.py         # Управление боем
├── equipment/
│   ├── enchantment_system.py     # Система зачарований
│   ├── gem_system.py             # Система камней и рун
│   └── equipment_manager.py      # Управление экипировкой
└── ui/
    ├── equipment_ui.py           # Интерфейс экипировки
    └── weapon_info_ui.py         # Информация об оружии
```

### Файлы для создания/изменения
- `src/core/ecs/combat_components.py` - компоненты боевой системы
- `src/combat/weapon_strategies.py` - стратегии использования оружия
- `src/combat/weapon_decorators.py` - декораторы улучшений оружия
- `src/combat/shield_states.py` - состояния щитов
- `src/combat/weapon_system.py` - система оружия (ECS System)
- `src/combat/shield_system.py` - система щитов (ECS System)
- `src/equipment/enchantment_system.py` - система зачарований
- `src/equipment/gem_system.py` - система камней и рун
- `src/entities/player.py` - экипировка игрока
- `src/ui/equipment_ui.py` - интерфейс экипировки

### Классы оружия
```python
class Weapon:
    def __init__(self, name, damage, speed, range, weapon_type):
        self.name = name
        self.damage = damage
        self.attack_speed = speed
        self.range = range
        self.type = weapon_type  # MELEE, RANGED, MAGIC

class Sword(Weapon):
    def __init__(self, sword_type):
        # SHORT, LONG, TWO_HANDED
        pass

class Crossbow(Weapon):
    def __init__(self):
        self.ammo_type = "bolts"
        self.reload_time = 1000  # ms
```

### Система характеристик оружия
- [ ] **Базовые характеристики**:
  - [ ] Урон (damage)
  - [ ] Скорость атаки (attack_speed)
  - [ ] Дальность (range)
  - [ ] Критический шанс (crit_chance)
- [ ] **Специальные свойства**:
  - [ ] Элементальный урон
  - [ ] Пробивание брони
  - [ ] Вампиризм (восстановление HP)
  - [ ] Особые эффекты при критах

### Конфигурация
```ini
[WEAPONS]
short_sword_damage = 15
long_sword_damage = 25
two_handed_sword_damage = 40
crossbow_damage = 35
bow_damage = 20

[SHIELDS]
wooden_shield_block = 50
metal_shield_block = 80
magic_shield_duration = 300000
```

### Интеграция с магической системой
- [ ] Зачарование оружия стихиями
- [ ] Магические посохи как оружие
- [ ] Комбинирование физических атак с заклинаниями
- [ ] Элементальные щиты против определенных стихий

## Критерии готовности
- [ ] Игрок может экипировать различные типы оружия
- [ ] Каждый тип оружия имеет уникальные характеристики
- [ ] Система щитов корректно блокирует урон
- [ ] Двуручное оружие блокирует использование щитов
- [ ] Магические щиты работают с системой маны
- [ ] Визуальные эффекты для всех типов оружия

## Приоритет
**Высокий** - Расширение основной боевой механики

## Зависимости
- Issue #03 (Система магии) - для магического оружия
- Текущая боевая система
- Система управления

## Балансировка
- Двуручное оружие: высокий урон, но нет защиты
- Одноручное + щит: средний урон, хорошая защита
- Двойные мечи: высокая скорость, средний урон
- Дальнобойное: высокий урон, но ограниченные боеприпасы

## Система прогрессии оружия
- [ ] **Редкость оружия**:
  - [ ] Обычное (белое)
  - [ ] Редкое (синее)
  - [ ] Эпическое (фиолетовое)
  - [ ] Легендарное (оранжевое)
- [ ] **Улучшение оружия**:
  - [ ] Заточка (+1, +2, +3...)
  - [ ] Зачарование элементами
  - [ ] Вставка камней (из Issue #08)

## Примерное время реализации
3-4 недели

## Связанные issues
- #03 (Система магии) - магическое оружие
- #06 (Дерево навыков) - ветки ближнего/дальнего боя
- #08 (Инвентарь) - хранение и управление оружием
- #09 (Квестовая система) - награды в виде оружия