# Игровой сценарий: "Последний Кузнец" - Акт I (Финальная техническая версия)
- **Версия:** 2.2 (Полная детализация)
- **Автор:** Gemini
- **Дата:** 2025-08-07

---

## <a name="toc"></a>Содержание Акта I

*   [**Пролог: Пепел и Искры**](#prologue)
    *   [Сцена 1: Последний урок](#prologue-scene1)
    *   [Сцена 2: Нападение](#prologue-scene2)
    *   [Сцена 3: Подземный побег](#prologue-scene3)
*   [**Глава 1: У реки**](#chapter1)
    *   [Сцена 1: Новый мир](#chapter1-scene1)
    *   [Сцена 2: Первая ночь](#chapter1-scene2)
*   [**Глава 2: Дорога домой**](#chapter2)
    *   [Сцена 1: Возвращение](#chapter2-scene1)
    *   [Сцена 2: Восстановление основ](#chapter2-scene2)
*   [**Глава 3: Город выживших**](#chapter3)
    *   [Сцена 1: Прибытие в "Приют"](#chapter3-scene1)
    *   [Сцена 2: Лицо из прошлого](#chapter3-scene2)
    *   [Сцена 3: Искра надежды](#chapter3-scene3)
*   [**Глава 4: Первые следы и первая искра**](#chapter4)
    *   [Сцена 1: Гиблые топи](#chapter4-scene1)
    *   [Сцена 2: Битва за брата](#chapter4-scene2)
    *   [Сцена 3: Таинственный лут](#chapter4-scene3)
*   [**Глава 5: Рефлексия у наковальни**](#chapter5)
    *   [Сцена 1: Возвращение домой и новая цель](#chapter5-scene1)
*   [**Навигация по сценарию**](#navigation)

---

## <a name="prologue"></a>Пролог: Пепел и Искры

### <a name="prologue-scene1"></a>Сцена 1: Последний урок
- **Локация:** Семейная кузня (Z=0)
- **Тип сцены:** Интерактивная кат-сцена / Обучение
- **Ключевая задача игрока:** Выковать свой первый предмет.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnGameStart`.
  - **Системные взаимодействия:** `QuestSystem.StartQuest("prologue_01_last_lesson", "Поговорить с отцом")`.

### <a name="prologue-scene2"></a>Сцена 2: Нападение
- **Локация:** Деревня, Кузня (Z=0)
- **Тип сцены:** Кат-сцена / Управляемый геймплей
- **Ключевая задача игрока:** Добраться до люка в подвал.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnQuestCompleted("prologue_01_last_lesson")`.
  - **Системные взаимодействия:** `WorldStateSystem.ChangeState("Peaceful" -> "Raid")`, `EnemySpawner.SpawnGroup("warchiefs_and_orcs")`, `DialogueSystem.PlayLine("father_final_words", "В тоннель! К реке! Не оглядывайся! Живи!")`, `OnInteract("tunnel_entrance_hatch")` запускает следующую сцену.

### <a name="prologue-scene3"></a>Сцена 3: Подземный побег
- **Локация:** Туннель под деревней (Z=-1)
- **Тип сцены:** Интерактивный геймплейный сегмент
- **Ключевая задача игрока:** Двигаться вперед до конца туннеля.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnInteract("tunnel_entrance_hatch")`.
  - **Системные взаимодействия:** `ZTransitionSystem.ChangePlayerZLevel(-1)`, `PlayerSystem.ConstrainToPath("escape_tunnel_path")`, `RenderingSystem.SetLayerVisibility("Z_-1", true)` и `RenderingSystem.SetLayerVisibility("Z_0", true)`, `OnPathEnd("escape_tunnel_path")` завершает сцену и пролог.

---

## <a name="chapter1"></a>Глава 1: У реки

### <a name="chapter1-scene1"></a>Сцена 1: Новый мир
- **Локация:** Берег реки, опушка леса (Z=0)
- **Тип сцены:** Геймплей / Обучение
- **Ключевая задача игрока:** Осмотреться и найти оружие.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnSceneStart` (после Пролога).
  - **Системные взаимодействия:** `ZTransitionSystem.ChangePlayerZLevel(0)`, `QuestSystem.StartQuest("act1_01_survivor", "Осмотритесь в поисках чего-нибудь полезного")`, интерактивные объекты `item_sturdy_branch` и `item_thorny_bush`.

### <a name="chapter1-scene2"></a>Сцена 2: Первая ночь
- **Локация:** Лес у реки (Z=0)
- **Тип сцены:** Геймплей / Выживание
- **Ключевая задача игрока:** Развести костер и пережить ночь.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnItemEquipped("weapon_club_makeshift")`.
  - **Системные взаимодействия:** `QuestSystem.UpdateObjective("act1_01_survivor", "Найдите место для лагеря и разведите костер")`, `WorldStateSystem.StartDayNightCycle()`.

---

## <a name="chapter2"></a>Глава 2: Дорога домой

### <a name="chapter2-scene1"></a>Сцена 1: Возвращение
- **Локация:** Окрестности родной деревни (Z=0)
- **Тип сцены:** Геймплей / Бой
- **Ключевая задача игрока:** Пробиться к руинам кузни.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnterZone("village_outskirts")`.
  - **Системные взаимодействия:** `WorldStateSystem.LoadMap("village_destroyed_populated")`, `EnemySpawner.SpawnGroup("bandits_level_1", 5)`.

### <a name="chapter2-scene2"></a>Сцена 2: Восстановление основ
- **Локация:** Руины кузни (Z=0)
- **Тип сцены:** Геймплей / Крафт
- **Ключевая задача игрока:** Восстановить кузню и выковать первый настоящий предмет.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnterZone("forge_ruins")`.
  - **Системные взаимодействия:** `QuestSystem.UpdateObjective("act1_02_road_home", "Соберите уцелевшие инструменты")`, `CraftingSystem.UnlockRecipe("recipe_iron_dagger")`, `OnItemCrafted("item_iron_dagger")` завершает квест.

---

## <a name="chapter3"></a>Глава 3: Город выживших

### <a name="chapter3-scene1"></a>Сцена 1: Прибытие в "Приют"
- **Локация:** Торговый город "Приют" (Z=0)
- **Тип сцены:** Исследование
- **Ключевая задача игрока:** Найти торговца Элиаса.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnQuestCompleted("act1_02_road_home")`.
  - **Системные взаимодействия:** `QuestSystem.StartQuest("main_03_rare_metals", "Отправляйтесь в Приют и найдите торговца Элиаса")`, `WorldStateSystem.LoadMap("city_hub")`.

### <a name="chapter3-scene2"></a>Сцена 2: Лицо из прошлого
- **Локация:** Лавка "Товары Элиаса" (Z=0)
- **Тип сцены:** Интерактивный диалог
- **Ключевая задача игрока:** Поговорить с торговцем.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnterZone("elias_shop")`.
  - **Системные взаимодействия:** `DialogueSystem.Start("elias_recognition_dialogue")`.

### <a name="chapter3-scene3"></a>Сцена 3: Искра надежды
- **Локация:** Лавка "Товары Элиаса" (Z=0)
- **Тип сцены:** Кат-сцена / Диалог
- **Ключевая задача игрока:** Узнать о выживших.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnDialogueNodeReached("elias_main_revelation")`.
  - **Системные взаимодействия:** `CutsceneSystem.Play("elias_story_flashback")`, `QuestSystem.StartQuest("main_04_family_hope", "Найдите следы на болотах")`.

---

## <a name="chapter4"></a>Глава 4: Первые следы и первая искра

### <a name="chapter4-scene1"></a>Сцена 1: Гиблые топи
- **Локация:** Старые Болота (Z=0)
- **Тип сцены:** Исследование / Бой
- **Ключевая задача игрока:** Найти 3 улики.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnterZone("swamp_entrance")`.
  - **Системные взаимодействия:** `WorldStateSystem.LoadMap("swamp_map")`, `EnemySpawner.SpawnGroup("swamp_creatures_level_1", 10)`.

### <a name="chapter4-scene2"></a>Сцена 2: Битва за брата
- **Локация:** Лагерь разбойников на болотах (Z=0)
- **Тип сцены:** Бой / Мини-босс
- **Ключевая задача игрока:** Победить главаря бандитов.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnAllCluesFound("main_04_family_hope")`.
  - **Системные взаимодействия:** `MapSystem.RevealLocation("bandit_camp")`, `EnemySpawner.Spawn("bandit_leader_boris")`.

### <a name="chapter4-scene3"></a>Сцена 3: Таинственный лут
- **Локация:** Лагерь разбойников (Z=0)
- **Тип сцены:** Открытие / Обучение через действие
- **Ключевая задача игрока:** Освободить брата и изучить добычу.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnemyKilled("bandit_leader_boris")`.
  - **Системные взаимодействия:** `CutsceneSystem.Play("freeing_the_brother")`, `LootSystem.DropSpecific(boss_id, ["item_notched_axe_socketed", "item_ember_amber"])`, `QuestSystem.StartQuest("discovery_01_strange_stones", "Этот камень делает оружие огненным. Нужно найти больше таких.")`.

---

## <a name="chapter5"></a>Глава 5: Рефлексия у наковальни

### <a name="chapter5-scene1"></a>Сцена 1: Возвращение домой и новая цель
- **Локация:** Восстановленная кузня (Z=0)
- **Тип сцены:** Диалог / Разблокировка системы исследований
- **Ключевая задача игрока:** Поговорить с братом и открыть новую цель.
- **Техническая реализация и геймплей:**
  - **Триггеры:** `OnEnterZone("home_forge_with_brother")`.
  - **Системные взаимодействия:** `DialogueSystem.Start("act1_final_dialogue")`, `OnDialogueNodeReached("player_realization_node")` -> `UISystem.UnlockFeature("Journal_Research_Tab")`, `QuestSystem.StartQuest("discovery_main_01_understanding_magic", "Узнать больше о природе магических камней")`.

---

## <a name="navigation"></a>Навигация по сценарию

*   **[К содержанию](./game_scenario_index.md)**
*   **[К Акту II](./game_scenario_act2_v0.1.md)** (файл будет создан)
