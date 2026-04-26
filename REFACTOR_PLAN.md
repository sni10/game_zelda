# REFACTOR_PLAN.md — Ревизия проекта и план разделения ответственности

**Ветка:** `feature/refactor`
**Дата:** 2026-04-26
**Цель:** привести проект к стандартам SOLID/SRP/ООП. Никаких "миров", ECS, порталов — только разделение ответственности там, где это критично.

---

## 📊 Топ файлов по LOC (на момент старта)

| LOC | Файл | Проблема (нарушение SRP) |
|---|---|---|
| **420** | `src/core/game.py` | God Object: цикл + ввод + рендер HUD + логирование + save/load роутинг |
| **350** | `src/core/config_loader.py` | Простыня ручных `_validate_*` методов на каждую секцию |
| **287** | `src/entities/player.py` | Контроллер + Модель (HP/оружия) + Рендер + Атака — всё в одном |
| **262** | `src/systems/enemy_manager.py` | Спавн + AI-оркестрация + урон + рендер + статистика |
| **209** | `src/world/world.py` | Карта + камера + коллизии + рендер фона + рендер overlay + миникарта |
| **205** | `src/world/terrain.py` | Тип + парсер ASCII + загрузчик файлов + рендер тайла |
| 182 | `src/entities/weapons.py` | OK (грамотно: ABC + 4 подкласса). **Не трогаем.** |
| 163 | `src/systems/save_system.py` | Сериализация + I/O + применение к объектам (терпимо, отложено) |

Остальные < 150 LOC — здоровы.

---

## 🚦 План работ (порядок коммитов)

Делаем мелкими коммитами на ветке `feature/refactor`, тесты прогоняем после каждого шага.

### ✅ Шаг 1. `game.py` → выделить `ui/hud.py` + `utils/session_logger.py`
**Цель:** −150 строк из `Game`, низкий риск.

- [ ] `src/ui/hud.py` — класс `HUD` с методами `draw_health_bar`, `draw_weapon_hud`, общий `draw(screen, player)`
- [ ] `src/utils/session_logger.py` — класс `SessionLogger` с `log(msg, level)`, открытие/закрытие файла
- [ ] `Game` использует `self.hud` и `self.logger` вместо собственных методов
- [ ] Прогнать `pytest tests/ -v`

### ⬜ Шаг 2. `world.py` → выделить `world/camera.py`
**Цель:** Камера — чистая математика, тестируется без pygame.

- [ ] `src/world/camera.py` — класс `Camera(x, y)` с `follow(target_x, target_y, screen_w, screen_h, world_w, world_h)`
- [ ] `World` делегирует камере, оставляет только данные карты + рендер
- [ ] Юнит-тесты на `Camera` (clamp по границам, центрирование)

### ⬜ Шаг 3. `terrain.py` → выделить `world/map_loader.py`
**Цель:** I/O отдельно от модели тайла (SRP).

- [ ] `src/world/map_loader.py` — функции `load_map_from_file`, `_parse_map_lines`, `_read_map_file`, `_overlay_path_for`
- [ ] `src/world/terrain.py` — только `TerrainType` + `TerrainTile` (data + draw)
- [ ] Обновить импорты в `world.py`

### ⬜ Шаг 4. `player.py` → выделить `PlayerStats` и `PlayerCombat`
**Цель:** разорвать God Object Player на тестируемые части.

- [ ] `PlayerStats` — HP, max_health, take_damage/heal, is_dead
- [ ] `PlayerCombat` — атака, attack_id, кулдаун, get_attack_rects
- [ ] `Player` — оркестратор: позиция + ссылки + draw
- [ ] Сохранить публичный API (`player.health`, `player.attacking` и т.д.) через `@property`-делегирование, чтобы не сломать save_system, enemy_manager, hud
- [ ] Юнит-тесты на `PlayerStats` отдельно

### ⛔ Откладываем (не блокирует фичи)
- **`enemy_manager.py` (262)** — внутренне когерентен, разделять не за чем. Вернёмся когда добавится aggro/таргетинг/AOE.
- **`config_loader.py` (350)** — раздут, но работает и оттестирован. Рефактор на dataclass-схему — отдельный спринт.

---

## 🔒 Правила работы на ветке

1. Один шаг = один коммит с понятным сообщением (`refactor(hud): extract HUD class from Game`).
2. После каждого шага: `pytest tests/ -v` — должно быть зелёное.
3. Публичный API классов (атрибуты, на которые ссылаются другие модули) **не ломаем**, либо мигрируем все use-sites в том же коммите.
4. **Никаких** новых фич в этой ветке. Только перестановка ответственности.
5. PR в `dev` после завершения шагов 1–4.

