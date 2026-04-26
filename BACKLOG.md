# 📋 BACKLOG — Zelda Game

Живой список задач: что чинить, что рефакторить, что добавлять.
Обновлять при каждой ревизии. Закрытые задачи переезжают в release notes.

> **Легенда приоритетов:**
> 🔴 Critical — ломает UX или блокирует разработку
> 🟡 Normal — важно, но не срочно
> 🟢 Nice to have — можно отложить

---

## 🐛 BUGS — что чинить

### 🔴 Сохранения работают наполовину
**Где:** `src/systems/save_system.py`, `src/core/game.py`
- [x] Меню «Загрузить игру» — теперь вызывает `quickload()` (вместо затирающего прогресс `start_new_game()`)
- [x] Убрана мёртвая строка `save_system.py:138` (артефакт рефакторинга `Player → PlayerStats`)
- [x] F9 восстанавливает `current_weapon_index` (и `iframe_timer`)
- [x] F9 восстанавливает живых врагов (тип/HP/позиция/cooldown) через `EnemyManager.serialize/deserialize`
- [x] F9 восстанавливает лежащие пикапы через `PickupManager.serialize/deserialize`
- [x] F9 восстанавливает `GameStats` через `GameStats.to_dict/from_dict` (вкл. play_time)
- [x] Валидация схемы JSON при загрузке (`SaveValidationError`) — порченный файл возвращает `None` без краша

### 🟡 Прочее
- [ ] При смерти игрока статистика на Game Over screen иногда показывает дублирующиеся записи (требует воспроизведения)

---

## 🔧 REFACTOR — технический долг

### 🟡 Незакрытые из ревизии (`REFACTOR_PLAN.md`)
- [ ] **`core/config_loader.py` (350 LOC)** — раздут от ручных `_validate_*`. Перевести на декларативную схему через `dataclasses` или `pydantic`.
- [ ] **`systems/enemy_manager.py` (262 LOC)** — на грани, отложено. Вернуться когда добавится таргетинг/aggro/AOE.
- [ ] **`world/world.py`** — ещё содержит рендер фона + миникарты. Можно вынести `world_renderer.py` отдельно.
- [ ] **`entities/player.py`** — после рефакторинга остался `draw()` ~50 строк с pygame. Если появятся спрайты — выделить `PlayerRenderer`.

### 🟢 Чистота кода
- [ ] Убрать `_PLAYER_HALF = 16` из `game.py` — вынести в config.ini как `PLAYER_SIZE`
- [ ] Унифицировать формат логирования: сейчас mix `print()` + `self.log()` + `SessionLogger`
- [ ] Pre-commit hooks: `black + flake8 + mypy` автоматически перед коммитом
- [ ] Conventional Commits lint в PR (`wagoid/commitlint-github-action`)

---

## 💾 SAVE/LOAD SYSTEM — отдельный эпик

### ✅ v0.3.1 — фикс существующего F9 (сделано)
1. [x] Убрана мёртвая строка `save_system.py:138`
2. [x] Сериализация `current_weapon_index` и `iframe_timer`
3. [x] `EnemyManager.serialize()` / `deserialize()` — живые враги с HP/позицией/cooldown + `target_counts`
4. [x] `PickupManager.serialize()` / `deserialize()` — лежащие пикапы (тип/x/y/lifetime)
5. [x] `GameStats.to_dict()` / `from_dict()` / `apply_dict()` — полное восстановление статистики (вкл. play_time)
6. [x] Валидация JSON-схемы (`_validate_save_data` + `SaveValidationError`)
7. [x] Round-trip тесты: `tests/unit/test_save_system_roundtrip.py` (8 тестов, вкл. legacy v1.0)

### ✅ v0.3.2 — UI слотов (сделано)

**Два типа сохранений (раздельно, не пересекаются):**
- **Quicksave (F5/F9)** — один файл `saves/quicksave.json`. Без подтверждений, без меню.
- **Manual saves (F6 + меню)** — до **10** слотов в `saves/manual/slot_01..10.json`. Создаются и загружаются только через меню.

**Реализация:**
1. [x] `SaveSystem.list_manual_saves()` — список manual-слотов с метаданными (timestamp, level, play_time, hp/max_hp, valid). Quicksave доступен отдельно через `get_quicksave_metadata()`.
2. [x] `src/ui/save_load_menu.py` — единый класс `SaveLoadMenu` с двумя режимами `MODE_LOAD`/`MODE_SAVE` (навигация ↑↓, Enter, Del, Esc, модалки overwrite/delete).
3. [x] Новые состояния `GameState.LOAD_MENU` и `GameState.SAVE_MENU`.
4. [x] **F5** = quicksave, **F9** = quickload (без изменений).
5. [x] **F6** = открыть SAVE_MENU; «Загрузить игру» из главного меню → LOAD_MENU со списком (quicksave-строка сверху, если есть, + manual-слоты).
6. [x] Лимит 10 manual-слотов; `save_to_slot` вне диапазона возвращает `False`.
7. [x] Подтверждение перезаписи занятого manual-слота (Y/N модалка); quicksave перезаписывается без подтверждения.
8. [x] Подтверждение удаления (Del → Y/N); quicksave удалить нельзя.
9. [ ] Превью миникарты в слоте (опц., отложено).

### ✅ v0.3.3 — Автосейв (сделано)

**Конфиг (`[autosave]` в `config.ini`):**
- `autosave_enabled` (default `true`) — глобальный выключатель.
- `autosave_interval_minutes` (default `5.0`) — интервал периодического автосейва.
- `autosave_limit` (default `3`) — максимум хранимых автосейвов, дальше ротация по mtime.
- `autosave_on_level_up` (default `true`) — отдельный триггер на level-up.

**Реализация:**
1. [x] `SaveSystem.autosave(player, world, ..., reason, limit)` — пишет в `saves/autosave/autosave_NN.json` с автоматическим выбором свободного слота (либо самого старого по mtime).
2. [x] `list_autosaves()` (свежие сверху) / `get_latest_autosave_metadata()` / `load_from_autosave(slot_id)` / `delete_autosave(slot_id)`.
3. [x] Поле `autosave_reason` в save_data → отображается в UI как «`(periodic)`», «`(level_up)`», ...
4. [x] Game: `_update_autosave(dt)` тикает таймер, ловит level-up по `player.level`, сбрасывается на `start_new_game`/`quickload`/`_apply_loaded_save_data`.
5. [x] `Game.trigger_autosave(reason)` — публичная точка для будущих триггеров (смена зоны и т.п.).
6. [x] `SaveLoadMenu.refresh()` подкладывает автосейвы в LOAD_MENU между quicksave и manual-слотами с лейблом «🕐 Автосохранение #NN (reason)».
7. [x] Enter в LOAD_MENU → `load_autosave`; Del → `delete_autosave` (через ту же модалку Y/N, что у manual).
8. [x] `MainMenu.has_saves()` теперь учитывает `saves/autosave/`.
9. [x] Тесты: `tests/unit/test_autosave.py` (10) — round-trip, ротация, сортировка, ротация по уменьшению лимита, удаление, has_saves; +3 UI-теста в `test_save_load_menu.py` (entries / Enter / Del-модалка для autosave).

---

## ✨ FEATURES — что добавлять

### 🟡 Близкое (v0.4.x)
- [ ] **Расширение оружия:** дальние (ствол с реальными снарядами),  заряженные удары - альтернативная стрельба
- [ ] **Инвентарь** и экран персонажа (`I`-key)
- [ ] **Магазин/торговец** — потратить накопленные монеты
- [ ] **бустеры** (HP, скорость, броня, урон)
- [ ] **Больше типов врагов** (5+): дальник-стрелок, чужой, чужой-боец, стая, мини-босс тяжелый
- [ ] **Sprite-анимация игрока** (4-8 кадров на направление) — заменить зелёный квадрат

### 🟢 Дальнее (v0.5+)
- [ ] **Боссы** с фазами и уникальными механиками
- [ ] **Звуковые эффекты** + фоновая музыка (`pygame.mixer`)
- [ ] **Сюжетный Акт I** — NPC, диалоги, квесты (база уже в `docs/scenario/`)
- [ ] **Возврат multi-world / Z-уровней** — но осознанно, на новой ветке, когда базовые механики стабильны
- [ ] **Локализация** (ru/en) через `i18n`-словари
- [ ] **Геймпад / xinput** поддержка
- [ ] **Particle system** (дым, искры от удара, кровь)

---

## 🧪 TESTING & QUALITY

- [ ] Покрытие 70% → 80% (сейчас ~73%)
- [ ] **Integration-тесты** в `tests/integration/` — папка есть, но пуста
- [ ] **Smoke-тест запуска игры** в headless-режиме (CI должен ловить регрессии main loop)
- [ ] Снять `mypy --strict` (сейчас обычный) — постепенно типизировать модули
- [ ] Бенчмарки FPS на больших картах (профилировщик `cProfile`)

---

## 📚 DOCS

- [ ] Обновить `README.md` под актуальные механики (Shift, оружия 1-4, пикапы)
- [ ] Перевести `AGENTS.md` под пост-multiworld реальность (там ещё описание ECS и WorldManager — устарело)
- [ ] Скриншоты текущей игры в `screenshots/` + добавить в README
- [ ] Архитектурная диаграмма (Mermaid) — какие классы кого вызывают

---

## 🚀 DEVOPS / CI

- [x] ✅ Накопительный bump версий по Conventional Commits (`versioning.yml`)
- [ ] Commitlint в PR — блокировать невалидные сообщения
- [ ] Build executable через `pyinstaller` для релизов на Windows/Linux/macOS
- [ ] Загрузка артефактов в GitHub Release автоматически
- [ ] Dependabot для обновления pygame и dev-зависимостей

---

## 🎯 Roadmap по версиям

| Версия | Тема | Что войдёт |
|--------|------|-----------|
| ✅ **v0.3.1** | Save/Load fix | Bug fixes из эпика «v0.3.1 — фикс F9» — **сделано** |
| ✅ **v0.3.2** | Save/Load UI | Слоты (10 manual + quicksave), LOAD/SAVE меню, F6 — **сделано** |
| ✅ **v0.3.3** | Autosave | Автосейвы (периодика + level-up) с ротацией по `autosave_limit` — **сделано** |
| **v0.4.0** | Inventory | Инвентарь, магазин, зелья |
| **v0.5.0** | Combat depth | Дальние оружия, магия, комбо, новые враги |
| **v0.6.0** | Audio + Sprites | Звук, музыка, анимация спрайтов |
| **v1.0.0** | Story Act I | Полноценный сюжетный Акт I |

---

**Последнее обновление:** 2026-04-27
**Сопровождает:** `REFACTOR_PLAN.md` (выполненные шаги)

