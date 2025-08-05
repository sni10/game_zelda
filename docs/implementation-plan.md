# План реализации новых фичей для Zelda-like Game

## Обзор

Данный документ содержит детальный план реализации четырех ключевых фичей для игры:

1. **Меню экран** - главное меню с опциями "Новая игра" и "Выход"
2. **Система смерти игрока** - обработка смерти при здоровье = 0 с геймовер экраном
3. **Система сохранений** - быстрое сохранение/загрузка по F5/F9
4. **Диалог выбора сейва** - интерфейс для выбора и загрузки сохранений

---

## 1. Меню экран (Main Menu)

### Описание
Создание главного меню игры с навигацией и базовыми опциями.

### Технические требования
- Отдельный класс `MainMenu` в `src/ui/menu.py`
- Состояния игры: `MENU`, `PLAYING`, `GAME_OVER`
- Навигация клавишами (стрелки вверх/вниз, Enter, Escape)
- Визуальное выделение активного пункта меню

### Структура меню
```
🎮 ZELDA-LIKE GAME
├── Новая игра
├── Продолжить игру (если есть сохранения)
├── Загрузить игру
└── Выход
```

### Файлы для создания/изменения
- `src/ui/__init__.py` - новый модуль
- `src/ui/menu.py` - класс MainMenu
- `src/core/game_states.py` - перечисление состояний игры
- `src/core/game.py` - интеграция состояний и меню

### Задачи
1. Создать систему состояний игры (GameState enum)
2. Реализовать класс MainMenu с отрисовкой и навигацией
3. Интегрировать меню в основной игровой цикл
4. Добавить переходы между состояниями
5. Стилизовать меню (шрифты, цвета, анимации)

---

## 2. Система смерти игрока (Death System)

### Описание
Обработка смерти игрока при достижении здоровья 0 с показом экрана Game Over.

### Технические требования
- Проверка `player.health <= 0` в игровом цикле
- Класс `GameOverScreen` в `src/ui/game_over.py`
- Блокировка управления игроком при смерти
- Автоматический переход в состояние `GAME_OVER`

### Структура Game Over экрана
```
💀 GAME OVER
├── "Вы погибли!"
├── Статистика (время игры, убито врагов, собрано предметов)
├── Вернуться в меню
└── Выйти из игры
```

### Файлы для создания/изменения
- `src/ui/game_over.py` - класс GameOverScreen
- `src/entities/player.py` - добавить метод is_dead()
- `src/core/game.py` - обработка смерти в игровом цикле
- `src/core/game_stats.py` - статистика игры

### Задачи
1. Добавить проверку смерти игрока в Game.update()
2. Создать GameOverScreen с информативным интерфейсом
3. Реализовать переход PLAYING -> GAME_OVER
4. Добавить систему игровой статистики
5. Реализовать возврат в главное меню

---

## 3. Система сохранений (Save System)

### Описание
Быстрая и надежная система сохранения/загрузки игрового прогресса.

### Технические требования
- Формат сохранения: JSON для читаемости и гибкости
- Папка сохранений: `saves/`
- Быстрое сохранение: F5 -> `quicksave.json`
- Быстрая загрузка: F9 -> загрузка `quicksave.json`
- Автосохранение при переходе между уровнями/зонами

### Структура сохранения
```json
{
  "version": "1.0",
  "timestamp": "2025-08-05T11:56:00Z",
  "player": {
    "x": 1000,
    "y": 1000,
    "health": 85,
    "max_health": 100,
    "facing_direction": "down"
  },
  "world": {
    "current_map": "main_world",
    "discovered_areas": ["spawn", "forest_entrance"]
  },
  "inventory": {
    "items": [],
    "gold": 0
  },
  "game_stats": {
    "play_time": 1234567,
    "enemies_killed": 5,
    "items_collected": 3
  }
}
```

### Файлы для создания/изменения
- `src/systems/save_system.py` - основная логика сохранений
- `src/core/game.py` - интеграция F5/F9, автосохранение
- `saves/` - папка для файлов сохранений
- `src/entities/player.py` - методы to_dict()/from_dict()
- `src/world/world.py` - сериализация состояния мира

### Задачи
1. Создать SaveSystem с методами save()/load()
2. Реализовать сериализацию игрока и мира
3. Добавить обработку F5/F9 в Game.handle_events()
4. Создать систему версионирования сохранений
5. Добавить обработку ошибок и валидацию
6. Реализовать автосохранение

---

## 4. Диалог выбора сейва (Save Selection Dialog)

### Описание
Интерфейс для просмотра, выбора и загрузки сохранений из главного меню.

### Технические требования
- Класс `SaveSelectionDialog` в `src/ui/save_dialog.py`
- Сканирование папки `saves/` для поиска файлов
- Отображение метаданных: дата, время игры, уровень игрока
- Навигация клавишами, подтверждение Enter
- Возможность удаления сохранений (Delete)

### Структура диалога
```
📁 ВЫБЕРИТЕ СОХРАНЕНИЕ

├── Quicksave          [05.08.2025 11:56]  Время: 20:34  HP: 85/100
├── Save Slot 1        [04.08.2025 15:30]  Время: 45:12  HP: 100/100
├── Save Slot 2        [03.08.2025 09:15]  Время: 12:45  HP: 60/100
├── [Пустой слот]
└── < Назад в меню >
```

### Файлы для создания/изменения
- `src/ui/save_dialog.py` - класс SaveSelectionDialog
- `src/systems/save_system.py` - методы get_save_list(), get_save_info()
- `src/ui/menu.py` - интеграция диалога в меню
- `src/core/game.py` - обработка загрузки выбранного сохранения

### Задачи
1. Создать SaveSelectionDialog с навигацией
2. Реализовать сканирование и парсинг сохранений
3. Добавить отображение метаданных сохранений
4. Интегрировать диалог в главное меню
5. Реализовать загрузку выбранного сохранения
6. Добавить возможность удаления сохранений

---

## GitHub Issues и структура веток

### Issue #1: Система состояний игры и главное меню
**Ветка:** `feature/main-menu`
**Приоритет:** High
**Описание:** Реализация системы состояний игры и главного меню с навигацией

**Задачи:**
- [ ] Создать enum GameState (MENU, PLAYING, GAME_OVER)
- [ ] Реализовать класс MainMenu
- [ ] Интегрировать меню в игровой цикл
- [ ] Добавить навигацию клавишами
- [ ] Стилизовать интерфейс меню

**Критерии приемки:**
- Игра запускается с главного меню
- Работает навигация стрелками и Enter
- Кнопка "Новая игра" запускает игру
- Кнопка "Выход" закрывает приложение
- ESC возвращает в меню из игры

### Issue #2: Система смерти игрока и Game Over экран
**Ветка:** `feature/death-system`
**Приоритет:** High
**Описание:** Обработка смерти игрока при здоровье = 0 с экраном Game Over

**Задачи:**
- [ ] Добавить проверку смерти в игровой цикл
- [ ] Создать GameOverScreen
- [ ] Реализовать переход в состояние GAME_OVER
- [ ] Добавить игровую статистику
- [ ] Реализовать возврат в главное меню

**Критерии приемки:**
- При health <= 0 игра переходит в Game Over
- Показывается экран с сообщением о смерти
- Отображается статистика игры
- Можно вернуться в главное меню
- Управление игроком блокируется при смерти

### Issue #3: Система быстрых сохранений F5/F9
**Ветка:** `feature/save-system`
**Приоритет:** High
**Описание:** Реализация системы сохранения/загрузки по клавишам F5/F9

**Задачи:**
- [ ] Создать SaveSystem с JSON сериализацией
- [ ] Реализовать сохранение состояния игрока и мира
- [ ] Добавить обработку F5 (сохранение) и F9 (загрузка)
- [ ] Создать систему версионирования сохранений
- [ ] Добавить обработку ошибок и валидацию
- [ ] Реализовать автосохранение

**Критерии приемки:**
- F5 сохраняет игру в quicksave.json
- F9 загружает последнее сохранение
- Сохраняется позиция, здоровье, состояние мира
- Обрабатываются ошибки загрузки/сохранения
- Показываются уведомления об успешном сохранении

### Issue #4: Диалог выбора и управления сохранениями
**Ветка:** `feature/save-dialog`
**Приоритет:** Medium
**Описание:** Интерфейс для выбора, загрузки и удаления сохранений

**Задачи:**
- [ ] Создать SaveSelectionDialog
- [ ] Реализовать сканирование папки saves/
- [ ] Добавить отображение метаданных сохранений
- [ ] Интегрировать диалог в главное меню
- [ ] Реализовать загрузку выбранного сохранения
- [ ] Добавить возможность удаления сохранений

**Критерии приемки:**
- В меню есть пункт "Загрузить игру"
- Показывается список всех сохранений с метаданными
- Работает навигация и выбор сохранения
- Можно загрузить выбранное сохранение
- Можно удалить сохранение клавишей Delete

---

## План коммитов и описания

### Feature: Main Menu System

```bash
# Ветка: feature/main-menu
git checkout -b feature/main-menu

# Коммиты:
feat: add game state system with enum
- Create GameState enum (MENU, PLAYING, GAME_OVER)
- Add state management to Game class
- Implement state transitions

feat: implement main menu class
- Create MainMenu class with navigation
- Add menu items (New Game, Continue, Load, Exit)
- Implement keyboard navigation (arrows, Enter, ESC)

feat: integrate menu into game loop
- Add menu rendering in MENU state
- Implement state transitions from menu
- Add menu background and styling

style: improve menu visual design
- Add custom fonts and colors
- Implement menu item highlighting
- Add smooth transitions and animations

test: add menu system tests
- Test state transitions
- Test menu navigation
- Test menu item selection

docs: update documentation for menu system
- Add menu system to architecture docs
- Update controls documentation
```

### Feature: Death System

```bash
# Ветка: feature/death-system
git checkout -b feature/death-system

# Коммиты:
feat: add death detection system
- Add is_dead() method to Player class
- Implement death check in game loop
- Add transition to GAME_OVER state

feat: create game over screen
- Implement GameOverScreen class
- Add death message and statistics display
- Implement return to menu functionality

feat: add game statistics tracking
- Create GameStats class
- Track play time, enemies killed, items collected
- Display stats on game over screen

fix: prevent player movement when dead
- Block input handling when player is dead
- Stop player updates in GAME_OVER state
- Ensure clean state transitions

test: add death system tests
- Test death detection
- Test game over screen functionality
- Test statistics tracking

docs: document death system
- Add death system to game mechanics docs
- Update player class documentation
```

### Feature: Save System

```bash
# Ветка: feature/save-system
git checkout -b feature/save-system

# Коммиты:
feat: create save system foundation
- Implement SaveSystem class
- Add JSON serialization for game state
- Create saves/ directory structure

feat: add player state serialization
- Implement Player.to_dict() and from_dict()
- Save position, health, and facing direction
- Add player state restoration

feat: add world state serialization
- Implement World.to_dict() and from_dict()
- Save world state and discovered areas
- Add world state restoration

feat: implement F5/F9 quick save/load
- Add F5 key handler for quick save
- Add F9 key handler for quick load
- Show save/load notifications

feat: add save versioning and validation
- Implement save file version checking
- Add data validation on load
- Handle corrupted save files gracefully

feat: implement autosave system
- Add periodic autosave functionality
- Save on important game events
- Configure autosave intervals

fix: improve save system error handling
- Add comprehensive error handling
- Show user-friendly error messages
- Prevent crashes on save/load failures

test: add save system tests
- Test save/load functionality
- Test data integrity
- Test error handling

docs: document save system
- Add save system architecture docs
- Document save file format
- Add troubleshooting guide
```

### Feature: Save Dialog

```bash
# Ветка: feature/save-dialog
git checkout -b feature/save-dialog

# Коммиты:
feat: create save selection dialog
- Implement SaveSelectionDialog class
- Add save file scanning functionality
- Create dialog navigation system

feat: add save metadata display
- Parse save file metadata
- Display creation date, play time, player stats
- Format metadata for user display

feat: integrate save dialog with menu
- Add "Load Game" menu item
- Connect dialog to main menu
- Implement dialog state management

feat: add save loading from dialog
- Implement save selection and loading
- Add confirmation dialogs
- Handle loading errors gracefully

feat: add save deletion functionality
- Implement save file deletion
- Add deletion confirmation
- Update dialog after deletion

style: improve save dialog UI
- Style save list display
- Add visual indicators for save status
- Implement smooth scrolling

test: add save dialog tests
- Test save scanning and parsing
- Test dialog navigation
- Test save loading and deletion

docs: document save dialog system
- Add save dialog to UI documentation
- Document save management features
```

---

## Порядок реализации

### Фаза 1: Основа (1-2 недели)
1. **Issue #1**: Система состояний и главное меню
2. **Issue #2**: Система смерти игрока

### Фаза 2: Сохранения (1-2 недели)  
3. **Issue #3**: Система быстрых сохранений F5/F9

### Фаза 3: Улучшения (1 неделя)
4. **Issue #4**: Диалог выбора сохранений

---

## Технические детали

### Архитектурные принципы
- **Модульность**: Каждая система в отдельном модуле
- **Расширяемость**: Легкое добавление новых состояний и функций
- **Надежность**: Обработка ошибок и валидация данных
- **Производительность**: Оптимизация сохранения/загрузки

### Структура файлов после реализации
```
src/
├── core/
│   ├── game.py (обновлен)
│   ├── game_states.py (новый)
│   └── game_stats.py (новый)
├── ui/
│   ├── __init__.py (новый)
│   ├── menu.py (новый)
│   ├── game_over.py (новый)
│   └── save_dialog.py (новый)
├── systems/
│   └── save_system.py (новый)
└── entities/
    └── player.py (обновлен)

saves/ (новая папка)
├── quicksave.json
├── save_slot_1.json
└── save_slot_2.json
```

### Зависимости
- Все фичи используют существующую конфигурационную систему
- Система сохранений зависит от сериализации игрока и мира
- Диалог сохранений зависит от системы сохранений
- Все UI компоненты используют единый стиль

---

## Заключение

Данный план обеспечивает поэтапную реализацию всех требуемых фичей с сохранением архитектурной целостности проекта. Каждая фича реализуется в отдельной ветке с детальными коммитами, что обеспечивает контролируемый процесс разработки и легкость интеграции.

Приоритет реализации: Меню → Смерть игрока → Сохранения → Диалог сохранений.