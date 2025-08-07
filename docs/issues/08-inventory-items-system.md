# Issue #08: Система инвентаря и предметов

## Описание
Реализация полноценной системы инвентаря с различными типами предметов, экипировкой и системой улучшений.

## Цель
Создать богатую систему предметов для глубокой RPG механики с коллекционированием, улучшением и стратегическим использованием.

## Требования

### Система инвентаря
- [ ] **Сетка предметов**: 10x6 слотов (60 слотов всего)
- [ ] **Категории предметов**:
  - [ ] Оружие (мечи, луки, посохи)
  - [ ] Броня (доспехи, щиты, аксессуары)
  - [ ] Расходуемые (зелья, еда, свитки)
  - [ ] Ключевые предметы (квестовые, ключи)
  - [ ] Материалы (руны, камни, ресурсы)
- [ ] **Функциональность**:
  - [ ] Перетаскивание предметов
  - [ ] Сортировка по категориям
  - [ ] Поиск и фильтрация
  - [ ] Быстрое использование (двойной клик)
  - [ ] Контекстное меню (ПКМ)

### Типы предметов

#### Расходуемые предметы
- [ ] **Зелья здоровья**:
  - [ ] Малое зелье: +25 HP
  - [ ] Среднее зелье: +50 HP
  - [ ] Большое зелье: +100 HP
  - [ ] Мгновенное действие
- [ ] **Зелья магии**:
  - [ ] Малое зелье: +25 MP
  - [ ] Среднее зелье: +50 MP
  - [ ] Большое зелье: +100 MP
  - [ ] Мгновенное действие
- [ ] **Комбо-зелья**:
  - [ ] Восстановление HP и MP одновременно
  - [ ] Эффективность: +50 HP, +50 MP
- [ ] **Зелья усиления**:
  - [ ] Зелье силы: +50% урон на 5 минут
  - [ ] Зелье защиты: +50% защита на 5 минут
  - [ ] Зелье скорости: +30% скорость на 3 минуты
- [ ] **Еда**:
  - [ ] Хлеб: +10 HP, дешевое восстановление
  - [ ] Мясо: +20 HP, среднее восстановление
  - [ ] Деликатесы: +30 HP + временные бонусы

#### Оружие и экипировка
- [ ] **Система редкости**:
  - [ ] Обычное (белое): базовые характеристики
  - [ ] Редкое (синее): +20% к характеристикам
  - [ ] Эпическое (фиолетовое): +50% + особые свойства
  - [ ] Легендарное (оранжевое): +100% + уникальные способности
- [ ] **Характеристики оружия**:
  - [ ] Базовый урон
  - [ ] Скорость атаки
  - [ ] Критический шанс
  - [ ] Дополнительные эффекты
- [ ] **Характеристики брони**:
  - [ ] Защита (уменьшение урона)
  - [ ] Бонусы к HP/MP
  - [ ] Сопротивления к стихиям
  - [ ] Особые свойства

#### Система улучшений (Diablo-стиль)
- [ ] **Руны**:
  - [ ] Руна силы: +урон
  - [ ] Руна защиты: +защита
  - [ ] Руна скорости: +скорость атаки
  - [ ] Руна магии: +магический урон
- [ ] **Камни**:
  - [ ] Камень огня: +огненный урон
  - [ ] Камень холода: +ледяной урон
  - [ ] Камень молнии: +урон молнией
  - [ ] Камень жизни: +вампиризм
- [ ] **Гнезда для улучшений**:
  - [ ] 1-3 гнезда в оружии/броне
  - [ ] Редкость влияет на количество гнезд
  - [ ] Возможность добавления гнезд за плату

#### Ключевые предметы
- [ ] **Квестовые предметы**:
  - [ ] Не занимают место в инвентаре
  - [ ] Автоматическое получение и использование
  - [ ] Связь с квестовой системой
- [ ] **Ключи и пропуски**:
  - [ ] Ключи от дверей и сундуков
  - [ ] Пропуски в закрытые области
  - [ ] Артефакты для активации порталов
- [ ] **Карты и схемы**:
  - [ ] Карты неизведанных областей
  - [ ] Схемы для крафтинга
  - [ ] Рецепты зелий

### Система крафтинга
- [ ] **Создание предметов**:
  - [ ] Комбинирование материалов
  - [ ] Рецепты для создания
  - [ ] Различные уровни сложности
- [ ] **Улучшение предметов**:
  - [ ] Заточка оружия (+1, +2, +3...)
  - [ ] Зачарование стихиями
  - [ ] Добавление гнезд для камней
- [ ] **Материалы**:
  - [ ] Металлы: железо, сталь, мифрил
  - [ ] Кристаллы: магические кристаллы стихий
  - [ ] Органика: кожа, кости, травы

### Быстрые слоты
- [ ] **Панель быстрого доступа**: F1-F8 (8 слотов)
- [ ] **Назначение предметов**: перетаскивание из инвентаря
- [ ] **Быстрое использование**: нажатие соответствующей клавиши
- [ ] **Визуальная индикация**: количество предметов, кулдауны

## Технические детали

### Архитектурные паттерны

#### ECS Components для системы предметов
```python
# src/core/ecs/inventory_components.py
class InventoryComponent(Component):
    """Компонент инвентаря"""
    def __init__(self, width: int = 10, height: int = 6):
        self.width = width
        self.height = height
        self.slots = [[None for _ in range(width)] for _ in range(height)]
        self.quick_slots = [None] * 8
        self.max_stack_size = 99

class ItemComponent(Component):
    """Компонент предмета"""
    def __init__(self, item_id: str, item_type: str, rarity: str):
        self.item_id = item_id
        self.item_type = item_type  # WEAPON, ARMOR, CONSUMABLE, KEY, MATERIAL
        self.rarity = rarity       # COMMON, RARE, EPIC, LEGENDARY
        self.stack_size = 1
        self.properties = {}
        self.enchantments = []
        self.sockets = []

class CraftingComponent(Component):
    """Компонент крафтинга"""
    def __init__(self):
        self.known_recipes = set()
        self.crafting_materials = {}
        self.crafting_queue = []

class EnhancementComponent(Component):
    """Компонент улучшений предмета"""
    def __init__(self):
        self.enhancement_level = 0  # +1, +2, +3...
        self.enchantments = []
        self.gems = []
        self.durability = 100
```

#### Factory Pattern для создания предметов
```python
# src/inventory/item_factory.py
class ItemFactory(ABC):
    """Абстрактная фабрика предметов"""
    
    @abstractmethod
    def create_item(self, item_type: str, rarity: str, level: int) -> Entity:
        pass

class WeaponFactory(ItemFactory):
    """Фабрика оружия"""
    def create_item(self, weapon_type: str, rarity: str, level: int) -> Entity:
        entity = Entity()
        
        # Базовые компоненты
        entity.add_component(ItemComponent(
            f"{weapon_type}_{rarity}_{level}",
            "WEAPON",
            rarity
        ))
        
        # Характеристики оружия в зависимости от типа
        if weapon_type == "sword":
            damage = self._calculate_weapon_damage("sword", rarity, level)
            entity.add_component(WeaponComponent("SWORD", damage, 1.0))
        elif weapon_type == "bow":
            damage = self._calculate_weapon_damage("bow", rarity, level)
            entity.add_component(WeaponComponent("BOW", damage, 0.8))
        
        # Добавление сокетов в зависимости от редкости
        sockets = self._get_socket_count(rarity)
        entity.add_component(EnhancementComponent())
        
        return entity

class ConsumableFactory(ItemFactory):
    """Фабрика расходуемых предметов"""
    def create_item(self, consumable_type: str, rarity: str, level: int) -> Entity:
        entity = Entity()
        
        entity.add_component(ItemComponent(
            f"{consumable_type}_{rarity}",
            "CONSUMABLE",
            rarity
        ))
        
        # Эффекты зелий
        if consumable_type == "health_potion":
            heal_amount = self._calculate_potion_power("health", rarity)
            entity.add_component(ConsumableComponent("HEAL", heal_amount))
        elif consumable_type == "mana_potion":
            mana_amount = self._calculate_potion_power("mana", rarity)
            entity.add_component(ConsumableComponent("RESTORE_MANA", mana_amount))
        
        return entity

class RandomLootFactory(ItemFactory):
    """Фабрика случайного лута"""
    def __init__(self, weapon_factory: WeaponFactory, consumable_factory: ConsumableFactory):
        self.weapon_factory = weapon_factory
        self.consumable_factory = consumable_factory
        self.loot_tables = self._load_loot_tables()
    
    def create_item(self, loot_source: str, rarity: str, level: int) -> Entity:
        # Выбор типа предмета по таблице лута
        item_type = self._roll_item_type(loot_source, rarity)
        
        if item_type in ["sword", "bow", "staff"]:
            return self.weapon_factory.create_item(item_type, rarity, level)
        elif item_type in ["health_potion", "mana_potion"]:
            return self.consumable_factory.create_item(item_type, rarity, level)
        
        return self._create_generic_item(item_type, rarity, level)
```

#### Decorator Pattern для улучшений предметов
```python
# src/inventory/item_decorators.py
class ItemDecorator(ABC):
    """Декоратор для улучшения предметов"""
    def __init__(self, item: Entity):
        self._item = item
    
    @abstractmethod
    def get_modified_property(self, property_name: str):
        pass

class EnchantmentDecorator(ItemDecorator):
    """Декоратор зачарований"""
    def __init__(self, item: Entity, enchantment_type: str, power: int):
        super().__init__(item)
        self.enchantment_type = enchantment_type
        self.power = power
    
    def get_modified_property(self, property_name: str):
        base_value = self._get_base_property(property_name)
        
        if self.enchantment_type == "SHARPNESS" and property_name == "damage":
            return base_value + (self.power * 5)
        elif self.enchantment_type == "FIRE" and property_name == "elemental_damage":
            return base_value + self.power
        
        return base_value

class EnhancementDecorator(ItemDecorator):
    """Декоратор заточки (+1, +2, +3...)"""
    def __init__(self, item: Entity, enhancement_level: int):
        super().__init__(item)
        self.enhancement_level = enhancement_level
    
    def get_modified_property(self, property_name: str):
        base_value = self._get_base_property(property_name)
        
        if property_name in ["damage", "defense", "magic_power"]:
            bonus = base_value * (self.enhancement_level * 0.1)
            return base_value + bonus
        
        return base_value

class GemDecorator(ItemDecorator):
    """Декоратор камней в сокетах"""
    def __init__(self, item: Entity, gems: List[GemComponent]):
        super().__init__(item)
        self.gems = gems
    
    def get_modified_property(self, property_name: str):
        base_value = self._get_base_property(property_name)
        
        for gem in self.gems:
            if gem.stat_type == property_name:
                base_value += gem.bonus_value
        
        return base_value
```

#### Composite Pattern для UI инвентаря
```python
# src/ui/inventory_ui_composite.py
class UIComponent(ABC):
    """Базовый компонент UI"""
    
    @abstractmethod
    def render(self, screen: Surface):
        pass
    
    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        pass

class UIContainer(UIComponent):
    """Контейнер UI компонентов"""
    def __init__(self):
        self.children = []
        self.position = (0, 0)
        self.size = (0, 0)
    
    def add_child(self, component: UIComponent):
        self.children.append(component)
    
    def remove_child(self, component: UIComponent):
        if component in self.children:
            self.children.remove(component)
    
    def render(self, screen: Surface):
        for child in self.children:
            child.render(screen)
    
    def handle_event(self, event: Event) -> bool:
        for child in self.children:
            if child.handle_event(event):
                return True
        return False

class InventoryGrid(UIContainer):
    """Сетка инвентаря"""
    def __init__(self, width: int, height: int, slot_size: int):
        super().__init__()
        self.width = width
        self.height = height
        self.slot_size = slot_size
        self.slots = []
        
        # Создание слотов
        for y in range(height):
            for x in range(width):
                slot = InventorySlot(x, y, slot_size)
                slot.position = (x * slot_size, y * slot_size)
                self.add_child(slot)
                self.slots.append(slot)

class InventorySlot(UIComponent):
    """Слот инвентаря"""
    def __init__(self, grid_x: int, grid_y: int, size: int):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.size = size
        self.item = None
        self.highlighted = False
        self.position = (0, 0)
    
    def render(self, screen: Surface):
        # Рендеринг фона слота
        slot_rect = pygame.Rect(self.position[0], self.position[1], self.size, self.size)
        color = (100, 100, 100) if not self.highlighted else (150, 150, 150)
        pygame.draw.rect(screen, color, slot_rect)
        
        # Рендеринг предмета
        if self.item:
            self._render_item(screen, self.item)
    
    def handle_event(self, event: Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            slot_rect = pygame.Rect(self.position[0], self.position[1], self.size, self.size)
            
            if slot_rect.collidepoint(mouse_pos):
                self._handle_slot_click(event.button)
                return True
        
        return False

class InventoryWindow(UIContainer):
    """Окно инвентаря"""
    def __init__(self, inventory_comp: InventoryComponent):
        super().__init__()
        self.inventory_comp = inventory_comp
        
        # Создание компонентов
        self.inventory_grid = InventoryGrid(
            inventory_comp.width,
            inventory_comp.height,
            64  # размер слота
        )
        
        self.quick_slots_bar = QuickSlotsBar(len(inventory_comp.quick_slots))
        self.item_info_panel = ItemInfoPanel()
        
        # Добавление в контейнер
        self.add_child(self.inventory_grid)
        self.add_child(self.quick_slots_bar)
        self.add_child(self.item_info_panel)
```

#### Strategy Pattern для крафтинга
```python
# src/inventory/crafting_strategies.py
class CraftingStrategy(ABC):
    """Стратегия крафтинга"""
    
    @abstractmethod
    def can_craft(self, recipe: Recipe, materials: dict) -> bool:
        pass
    
    @abstractmethod
    def craft_item(self, recipe: Recipe, materials: dict) -> Entity:
        pass

class BasicCraftingStrategy(CraftingStrategy):
    """Базовая стратегия крафтинга"""
    def can_craft(self, recipe: Recipe, materials: dict) -> bool:
        for material_id, required_amount in recipe.required_materials.items():
            if materials.get(material_id, 0) < required_amount:
                return False
        return True
    
    def craft_item(self, recipe: Recipe, materials: dict) -> Entity:
        if not self.can_craft(recipe, materials):
            return None
        
        # Создание предмета
        item = self.item_factory.create_item(
            recipe.result_item_type,
            recipe.result_rarity,
            recipe.result_level
        )
        
        # Потребление материалов
        for material_id, required_amount in recipe.required_materials.items():
            materials[material_id] -= required_amount
        
        return item

class EnhancementCraftingStrategy(CraftingStrategy):
    """Стратегия улучшения предметов"""
    def craft_item(self, recipe: Recipe, materials: dict) -> Entity:
        base_item = materials.get("base_item")
        enhancement_materials = materials.get("enhancement_materials", [])
        
        if not base_item:
            return None
        
        # Применение улучшений
        enhanced_item = EnhancementDecorator(base_item, recipe.enhancement_level)
        
        # Добавление зачарований
        for enchantment in recipe.enchantments:
            enhanced_item = EnchantmentDecorator(enhanced_item, enchantment.type, enchantment.power)
        
        return enhanced_item
```

### Структурные изменения проекта

#### Новая структура папок
```
src/
├── core/ecs/
│   └── inventory_components.py   # Компоненты инвентаря и предметов
├── inventory/
│   ├── item_factory.py           # Фабрики предметов (Factory Pattern)
│   ├── item_decorators.py        # Декораторы улучшений (Decorator Pattern)
│   ├── crafting_strategies.py    # Стратегии крафтинга (Strategy Pattern)
│   ├── inventory_system.py       # Система инвентаря (ECS System)
│   ├── crafting_system.py        # Система крафтинга (ECS System)
│   └── loot_system.py            # Система лута (ECS System)
├── ui/
│   ├── inventory_ui_composite.py # UI инвентаря (Composite Pattern)
│   ├── crafting_ui.py            # Интерфейс крафтинга
│   └── item_tooltip.py           # Подсказки предметов
└── data/
    ├── items/                    # Конфигурации предметов
    ├── recipes/                  # Рецепты крафтинга
    └── loot_tables/              # Таблицы лута
```

### Файлы для создания/изменения
- `src/core/ecs/inventory_components.py` - компоненты инвентаря и предметов
- `src/inventory/item_factory.py` - фабрики предметов (Factory Pattern)
- `src/inventory/item_decorators.py` - декораторы улучшений (Decorator Pattern)
- `src/inventory/crafting_strategies.py` - стратегии крафтинга (Strategy Pattern)
- `src/inventory/inventory_system.py` - система инвентаря (ECS System)
- `src/inventory/crafting_system.py` - система крафтинга (ECS System)
- `src/ui/inventory_ui_composite.py` - UI инвентаря (Composite Pattern)
- `src/ui/crafting_ui.py` - интерфейс крафтинга
- `src/ui/item_tooltip.py` - подсказки предметов

### Архитектура системы предметов
```python
class Item:
    def __init__(self, name, item_type, rarity, properties):
        self.name = name
        self.type = item_type  # WEAPON, ARMOR, CONSUMABLE, KEY, MATERIAL
        self.rarity = rarity   # COMMON, RARE, EPIC, LEGENDARY
        self.properties = properties
        self.sockets = []      # для улучшений
        self.stack_size = 1    # количество в стаке
        
class Inventory:
    def __init__(self, width=10, height=6):
        self.width = width
        self.height = height
        self.slots = [[None for _ in range(width)] for _ in range(height)]
        self.quick_slots = [None] * 8
        
    def add_item(self, item, quantity=1):
        # Логика добавления предмета
        pass
        
    def remove_item(self, item, quantity=1):
        # Логика удаления предмета
        pass
```

### Конфигурация
```ini
[INVENTORY]
width = 10
height = 6
max_stack_size = 99
quick_slots = 8

[ITEM_RARITY]
common_color = 255,255,255
rare_color = 100,149,237
epic_color = 138,43,226
legendary_color = 255,165,0

[CRAFTING]
success_chance_base = 80
material_consumption = 1
upgrade_cost_multiplier = 1.5
```

### Интеграция с другими системами
- [ ] **Боевая система**: применение характеристик оружия
- [ ] **Магическая система**: магические предметы и посохи
- [ ] **Система здоровья**: зелья и еда
- [ ] **Квестовая система**: квестовые предметы
- [ ] **Система сохранений**: сохранение инвентаря
- [ ] **Event система**: дроп предметов из сундуков

### Интерфейс инвентаря
- [ ] **Открытие**: клавиша I (Inventory)
- [ ] **Визуализация**:
  - [ ] Сетка слотов с иконками предметов
  - [ ] Цветовая индикация редкости
  - [ ] Количество предметов в стаке
  - [ ] Подсказки при наведении
- [ ] **Взаимодействие**:
  - [ ] Перетаскивание предметов
  - [ ] Разделение стаков
  - [ ] Быстрое использование
  - [ ] Сортировка и фильтрация

## Критерии готовности
- [ ] Инвентарь корректно хранит и отображает предметы
- [ ] Все типы предметов функциональны
- [ ] Система улучшений работает
- [ ] Быстрые слоты функциональны
- [ ] Крафтинг позволяет создавать предметы
- [ ] Интерфейс интуитивно понятен
- [ ] Система сохраняет состояние инвентаря

## Приоритет
**Высокий** - Критически важно для RPG механик

## Зависимости
- Issue #04 (Оружие) - для оружейных предметов
- Issue #05 (Враги) - для дропа предметов
- Issue #07 (Event boxes) - для сундуков с лутом
- Текущая система здоровья

## Балансировка
- Редкие предметы должны быть значительно лучше обычных
- Зелья не должны быть слишком дешевыми или дорогими
- Крафтинг должен требовать усилий, но давать хорошие результаты
- Инвентарь должен быть достаточно большим, но не бесконечным

## Примерное время реализации
4-5 недель

## Связанные issues
- #04 (Оружие) - оружейные предметы
- #05 (Враги) - дроп предметов
- #07 (Event boxes) - лут из сундуков
- #09 (Квесты) - квестовые предметы

---

## Подзадачи для реализации

### 🎒 Фаза 1: Базовая архитектура инвентаря
**Цель**: Создание ECS компонентов и базовой структуры инвентаря

#### 1.1 ECS компоненты инвентаря
- [ ] Создать `src/core/ecs/inventory_components.py` - InventoryComponent, ItemComponent
- [ ] Создать CraftingComponent, EnhancementComponent
- [ ] Создать `test_inventory_components.py` - unit тесты компонентов инвентаря
- [ ] Все компоненты инвентаря работают с базовой функциональностью

#### 1.2 Система инвентаря как ECS System
- [ ] Создать `src/inventory/inventory_system.py` - InventorySystem (ECS System)
- [ ] Операции добавления, удаления, перемещения предметов
- [ ] Создать `test_inventory_system.py` - тестирование системы инвентаря
- [ ] Инвентарь корректно управляет предметами

#### 1.3 Интеграция инвентаря с игроком
- [ ] Обновить `src/entities/player.py` - добавить InventoryComponent
- [ ] Создать базовые операции работы с инвентарем
- [ ] Создать `test_player_inventory.py` - тестирование инвентаря игрока
- [ ] Игрок может хранить и управлять предметами

### 🏭 Фаза 2: Factory Pattern для создания предметов
**Цель**: Создание различных типов предметов через фабрики

#### 2.1 Базовая фабрика предметов
- [ ] Создать `src/inventory/item_factory.py` - ItemFactory, WeaponFactory, ConsumableFactory
- [ ] Создание предметов по типу и параметрам
- [ ] Создать `test_item_factory.py` - тестирование фабрик предметов
- [ ] Фабрики корректно создают все типы предметов

#### 2.2 Система редкости и случайной генерации
- [ ] Создать RandomLootFactory для генерации случайного лута
- [ ] Система редкости: обычное, редкое, эпическое, легендарное
- [ ] Создать `test_random_loot.py` - тестирование случайной генерации
- [ ] Лут генерируется с соответствующими характеристиками

#### 2.3 Загрузка предметов из конфигурации
- [ ] Создать систему загрузки предметов из JSON файлов
- [ ] Валидация параметров предметов
- [ ] Создать `test_item_loading.py` - тестирование загрузки предметов
- [ ] Предметы корректно загружаются из конфигурационных файлов

### 💉 Фаза 3: Расходуемые предметы и зелья
**Цель**: Реализация зелий, еды и временных усилений

#### 3.1 Система зелий здоровья и маны
- [ ] Реализовать HealthPotionItem - малое/среднее/большое зелье здоровья
- [ ] Реализовать ManaPotionItem - зелья восстановления маны
- [ ] Создать `test_healing_items.py` - тестирование зелий лечения
- [ ] Зелья корректно восстанавливают здоровье и ману

#### 3.2 Комбо-зелья и усиления
- [ ] Реализовать ComboPotionItem - восстановление HP и MP одновременно
- [ ] Создать BuffPotionItem - зелья силы, защиты, скорости
- [ ] Создать `test_buff_items.py` - тестирование зелий усиления
- [ ] Зелья усиления дают временные бонусы

#### 3.3 Система еды
- [ ] Реализовать FoodItem - хлеб, мясо, деликатесы
- [ ] Различные уровни восстановления и бонусов
- [ ] Создать `test_food_items.py` - тестирование системы еды
- [ ] Еда предоставляет дешевое восстановление с бонусами

### ✨ Фаза 4: Система улучшений предметов (Diablo-стиль)
**Цель**: Decorator Pattern для модификации предметов

#### 4.1 Базовые декораторы предметов
- [ ] Создать `src/inventory/item_decorators.py` - ItemDecorator, EnchantmentDecorator
- [ ] Создать EnhancementDecorator, GemDecorator
- [ ] Создать `test_item_decorators.py` - тестирование декораторов предметов
- [ ] Улучшения корректно модифицируют характеристики предметов

#### 4.2 Система рун и камней
- [ ] Реализовать RuneItem - руны силы, защиты, скорости, магии
- [ ] Реализовать GemItem - камни огня, холода, молнии, жизни
- [ ] Создать `test_enhancement_items.py` - тестирование рун и камней
- [ ] Руны и камни дают соответствующие бонусы

#### 4.3 Система сокетов в предметах
- [ ] Добавить поддержку сокетов в оружии и броне
- [ ] Механика вставки и извлечения камней/рун
- [ ] Создать `test_socket_system.py` - тестирование системы сокетов
- [ ] Сокеты корректно принимают и применяют эффекты улучшений

### 🔨 Фаза 5: Система крафтинга
**Цель**: Strategy Pattern для создания и улучшения предметов

#### 5.1 Базовые стратегии крафтинга
- [ ] Создать `src/inventory/crafting_strategies.py` - CraftingStrategy, BasicCraftingStrategy
- [ ] Создать EnhancementCraftingStrategy для улучшения предметов
- [ ] Создать `test_crafting_strategies.py` - тестирование стратегий крафтинга
- [ ] Каждая стратегия крафтинга работает по своим правилам

#### 5.2 Система рецептов
- [ ] Создать RecipeComponent для хранения рецептов крафтинга
- [ ] Загрузка рецептов из конфигурационных файлов
- [ ] Создать `test_crafting_recipes.py` - тестирование рецептов
- [ ] Рецепты правильно определяют требования и результаты

#### 5.3 Система крафтинга как ECS System
- [ ] Создать `src/inventory/crafting_system.py` - CraftingSystem (ECS System)
- [ ] Интеграция с инвентарем для потребления материалов
- [ ] Создать `test_crafting_system.py` - тестирование системы крафтинга
- [ ] Система крафтинга создает предметы по рецептам

### 🎮 Фаза 6: Пользовательский интерфейс инвентаря
**Цель**: Composite Pattern для UI инвентаря

#### 6.1 Сетка инвентаря
- [ ] Создать `src/ui/inventory_ui_composite.py` - UIContainer, InventoryGrid, InventorySlot
- [ ] Сетка 10x6 слотов с перетаскиванием
- [ ] Создать `test_inventory_grid.py` - тестирование сетки инвентаря
- [ ] Удобный интерфейс для управления предметами

#### 6.2 Система быстрых слотов
- [ ] Создать QuickSlotsBar - панель быстрых слотов F1-F8
- [ ] Назначение предметов из инвентаря на быстрые клавиши
- [ ] Создать `test_quick_slots.py` - тестирование быстрых слотов
- [ ] Быстрые слоты позволяют мгновенно использовать предметы

#### 6.3 Подсказки и информация о предметах
- [ ] Создать `src/ui/item_tooltip.py` - всплывающие подсказки предметов
- [ ] Отображение характеристик, редкости, улучшений
- [ ] Создать `test_item_tooltips.py` - тестирование подсказок
- [ ] Подсказки показывают полную информацию о предметах

### 🔧 Фаза 7: Интеграция и специальные предметы
**Цель**: Ключевые предметы и интеграция систем

#### 7.1 Система ключевых предметов
- [ ] Создать KeyItemComponent для квестовых предметов
- [ ] Автоматическое получение и использование ключевых предметов
- [ ] Создать `test_key_items.py` - тестирование ключевых предметов
- [ ] Ключевые предметы не занимают место и автоматически используются

#### 7.2 Система дропа предметов
- [ ] Создать `src/inventory/loot_system.py` - LootSystem (ECS System)
- [ ] Интеграция с системой врагов и Event Boxes
- [ ] Создать `test_loot_system.py` - тестирование дропа предметов
- [ ] Предметы корректно дропаются с врагов и из сундуков

#### 7.3 Интерфейс крафтинга
- [ ] Создать `src/ui/crafting_ui.py` - окно крафтинга
- [ ] Отображение доступных рецептов и материалов
- [ ] Создать `test_crafting_ui.py` - тестирование UI крафтинга
- [ ] Удобный интерфейс для создания предметов

### 🔧 Фаза 8: Интеграция и оптимизация
**Цель**: Финальная интеграция со всеми системами

#### 8.1 Интеграция с боевыми системами
- [ ] Связать предметы с системой оружия и магии
- [ ] Автоматическое применение бонусов от экипированных предметов
- [ ] Создать `test_item_combat_integration.py` - интеграционные тесты
- [ ] Предметы корректно влияют на боевые характеристики

#### 8.2 Система сортировки и фильтрации
- [ ] Реализовать автоматическую сортировку предметов по типу/редкости
- [ ] Система поиска и фильтрации в инвентаре
- [ ] Создать `test_inventory_organization.py` - тестирование организации инвентаря
- [ ] Игрок может легко найти нужные предметы

#### 8.3 Конфигурация и балансировка
- [ ] Добавить настройки предметов в `config.ini` - характеристики, редкость, цены
- [ ] Создать `test_item_balance.py` - тесты игрового баланса предметов
- [ ] Создать документацию по системе предметов в `CLAUDE.md`
- [ ] Система предметов сбалансирована и документирована

---

## 🌳 Дерево зависимостей подзадач

```
Фаза 1: Базовая архитектура инвентаря
├── 1.1 ECS компоненты инвентаря
├── 1.2 Система инвентаря (зависит от 1.1)
└── 1.3 Интеграция с игроком (зависит от 1.1, 1.2)

Фаза 2: Factory Pattern для предметов
├── 2.1 Базовая фабрика предметов (зависит от 1.1)
├── 2.2 Система редкости (зависит от 2.1)
└── 2.3 Загрузка из конфигурации (зависит от 2.2)

Фаза 3: Расходуемые предметы
├── 3.1 Зелья здоровья и маны (зависит от 2.1)
├── 3.2 Комбо-зелья и усиления (зависит от 3.1)
└── 3.3 Система еды (зависит от 3.1)

Фаза 4: Система улучшений (может выполняться параллельно после Фазы 2)
├── 4.1 Декораторы предметов (зависит от 1.1, 2.1)
├── 4.2 Руны и камни (зависит от 4.1)
└── 4.3 Система сокетов (зависит от 4.2)

Фаза 5: Система крафтинга
├── 5.1 Стратегии крафтинга (зависит от 2.1, 4.1)
├── 5.2 Система рецептов (зависит от 5.1)
└── 5.3 Система крафтинга (зависит от 5.2, 1.2)

Фаза 6: UI инвентаря
├── 6.1 Сетка инвентаря (зависит от 1.3)
├── 6.2 Быстрые слоты (зависит от 6.1)
└── 6.3 Подсказки предметов (зависит от 6.1, 4.1)

Фаза 7: Специальные предметы
├── 7.1 Ключевые предметы (зависит от 1.1, Issue #09)
├── 7.2 Система дропа (зависит от 2.2, Issue #05, #07)
└── 7.3 Интерфейс крафтинга (зависит от 5.3, 6.1)

Фаза 8: Интеграция и оптимизация
├── 8.1 Интеграция с боем (зависит от всех предыдущих фаз, Issue #04)
├── 8.2 Организация инвентаря (зависит от 6.1)
└── 8.3 Конфигурация (зависит от всех предыдущих фаз)
```

**Критический путь**: 1.1 → 1.2 → 1.3 → 2.1 → 6.1 → 8.1 → 8.3

**Минимальные требования к тестированию**: 
- Unit тесты для каждого типа предмета и компонента инвентаря
- Интеграционные тесты для взаимодействия с боевыми системами
- Тесты производительности при большом количестве предметов
- Минимальное покрытие: 90% для критических компонентов инвентаря