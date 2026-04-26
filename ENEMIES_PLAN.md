# 👹 Enemies Sprint Plan

> **Временный документ.** Удалить после завершения фичи и мерджа.
> Цель: сделать игру "живой" — добавить врагов, чтобы оружие реально что-то убивало.

## ⚙️ Решённые вопросы

| # | Решение |
|---|---------|
| 1 | HP — обязательно. У каждого врага. |
| 2 | Архитектура: Strategy (AI) + Factory (создание). Расширение без правки существующего кода (OCP). |
| 3 | Враги патрулируют зону **4 тайла** от точки спавна, **без** реакции на игрока (для MVP). |
| 4 | Контактный урон врагов игроку — **отложен на пост-MVP**. |

Дополнительно:
- **3 типа врагов** для MVP: `LightEnemy`, `HeavyEnemy`, `FastEnemy`.
- **Спавн** вне зоны видимости (≥ 1 экран от игрока).
- HP: light=1, heavy=3, fast=1 удар(а) от меча.
- Один взмах оружия = один урон каждому врагу (не каждый кадр атаки).

## 🏗️ Архитектура

```
src/entities/
├── enemy.py          — Enemy база + LightEnemy/HeavyEnemy/FastEnemy
├── enemy_ai.py       — AIBehavior (Strategy): PatrolBehavior, IdleBehavior
└── enemy_factory.py  — EnemyFactory (регистр типов + создание)

src/systems/
└── enemy_manager.py  — EnemyManager: спавн, update, draw, apply_player_attack
```

**Принципы:**
- **OCP**: добавление 50-го типа = новый подкласс + регистрация в фабрике, без правки старого кода
- **Composition over inheritance**: Enemy агрегирует `EnemyStats` (баланс) + `AIBehavior` (поведение)
- **Config-first**: статы врагов в `config.ini`, не в коде
- Лимит на патруль: `patrol_zone: pygame.Rect` 4×4 тайла вокруг точки спавна

## ✅ Чек-лист

### Этап 0 — Подготовка
- [x] Создать ветку `feature/enemies` от текущего состояния
- [x] Конфиг `[enemies]` в `config.ini` со статами 3 типов и параметрами спавна
- [x] Валидация конфига в `ConfigLoader`

### Этап 1 — Фундамент
- [x] `EnemyStats` (dataclass) — статы врага из конфига
- [x] `AIBehavior` (ABC) + `PatrolBehavior` + `IdleBehavior`
- [x] `Enemy` базовый класс: HP, rect, take_damage, is_dead, update→AI, draw
- [x] `LightEnemy`, `HeavyEnemy`, `FastEnemy` подклассы (различия только в статах/цвете/AI)

### Этап 2 — Фабрика и менеджер
- [x] `EnemyFactory.register(type_id, factory_callable)` + `create(type_id, x, y, patrol_zone)`
- [x] Регистрация 3 типов на module-load
- [x] `EnemyManager`: список, update(dt, world), draw, spawn_random_outside_view(player, count_by_type)
- [x] Алгоритм спавна: случайная точка мира → вне зоны видимости → проходимый тайл (повтор до 50 попыток)

### Этап 3 — Геймплей-цикл
- [x] `Player.attack_id` — увеличивается при каждом новом взмахе
- [x] `Enemy.last_hit_attack_id` — чтобы 1 атака = 1 урон врагу
- [x] `EnemyManager.apply_player_attack(player, weapon)` → возвращает `(hits, kills)`
- [x] `Game.update()`: при атаке → apply_player_attack → game_stats.enemies_killed
- [x] Удаление мёртвых из менеджера

### Этап 4 — UX
- [x] HP-bar над врагом (только если HP < max)
- [x] Кратковременный flash-эффект при попадании (краснеет на 100мс)
- [x] Debug: количество живых врагов

### Этап 5 — Интеграция
- [x] `World.enemy_manager` (или передача через Game) — wiring
- [x] Спавн при старте новой игры: 6 light + 2 heavy + 4 fast
- [x] `Game.draw()` рисует врагов между землёй и игроком (или отдельным слоем)

### Этап 6 — Тесты
- [x] `test_enemies.py` — HP, урон, смерть, AI, фабрика, менеджер (22 теста)
- [x] Прогон всей сюиты: **148 passed** (было 126 + 22 новых)

### Этап 7 — Финал
- [x] Smoke-test: запуск игры, спавн 12 врагов, бой
- [ ] Удалить этот файл (`ENEMIES_PLAN.md`) — после ревью пользователем
- [ ] Дать пользователю на ревью и коммит

## 🐛 Пост-MVP фиксы (после первой проверки)

### Баланс оружия
- [x] Урон оружий приведён к шкале HP (1 удар = 1 HP):
      Sword=1, Spear=1, Bow=1, Bomb=3 (убивает Heavy с одного взрыва)
- [x] Heavy теперь действительно держит 3 удара мечом (баг подтверждён фиксом)

### Patrol-движение
- [x] `PatrolBehavior` теперь **только axial** — выбирает горизонталь ИЛИ вертикаль,
      без диагоналей. Враги двигаются плавно "влево-вниз-вверх-вправо",
      а не хаотично "как мухи".
- [x] Тест `test_patrol_axial_only_no_diagonals` — 50 кадров без единой диагонали

### Авто-респавн
- [x] `EnemyManager.target_counts` запоминает целевую численность из `spawn_initial()`
- [x] `update(dt, player_x, player_y)` каждые `respawn_interval` сек. (5 по умолчанию)
      пытается доспавнить недостающих
- [x] Респавн соблюдает `spawn_min_distance` — игрок видит "новых" врагов
      только когда отошёл от зачищенной зоны
- [x] Конфиг: `respawn_interval = 5.0` в `[enemies]`
- [x] Тесты: `test_respawn_restores_count_when_player_far` + `test_respawn_does_not_happen_near_player`

### Прочее
- [x] Sprint по Shift (×1.8 скорости), 5 тестов
- [x] **156/156 passed** после всех правок

## 🔮 Что осознанно НЕ делаем сейчас

- Преследование игрока (Chase AI) — пост-MVP
- Контактный урон от врагов — пост-MVP
- Дроп предметов с врагов — отдельная фича (Items)
- Спрайты врагов — пока геометрия (квадраты разного цвета/размера)
- Звуки удара/смерти — отдельная фича (Sound)
- Респавн — пост-MVP (умерли — мир пустой)

