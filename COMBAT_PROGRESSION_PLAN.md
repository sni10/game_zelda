# ⚔️ Combat Loop & Progression — Sprint Plan

> **Временный документ.** Удалить после мерджа фичи.
> **Цель:** замкнуть боевую петлю (враги бьют в ответ → можно умереть) и поверх неё положить классическую RPG-прогрессию: дроп сердечек, монет и опыта с врагов, уровни игрока с ростом урона и максимального HP.
> **Без инвентаря.** Монеты — просто счётчик. Сердечки — мгновенный хил. Опыт — прокачка статов.

**Ветка:** `feature/combat-loop`
**Базовая ветка:** `dev`
**Дата старта:** 2026-04-26

---

## 🧭 Принципы

- **Config-first.** Все числа (урон врагов, i-frame, цена уровня, hp/lvl) — в `config.ini`, валидация в `ConfigLoader`.
- **SOLID/SRP.** Не раздуваем существующие God-объекты. Новые ответственности — в новых модулях.
- **Composition over inheritance.** AI добавляем как новую Strategy, прогрессию — отдельным компонентом игрока.
- **OCP по AI:** добавление нового поведения = новый класс, без правки `PatrolBehavior`/`IdleBehavior`.
- **Тесты после каждого этапа.** Минимум 70% coverage держим.
- **Никаких миров/ECS/Z-уровней** — этот проект плоский, как и решено в `REFACTOR_PLAN.md`.

---

## 🎯 Скоуп фичи (что входит)

### Часть A. Замыкание боя
1. **ChaseBehavior** — враг видит игрока в радиусе и идёт к нему, теряет → возвращается на patrol-точку.
2. **Контактный урон** — при пересечении хитбоксов враг наносит урон игроку.
3. **i-frames** — после получения урона игрок неуязвим N мс (мигает).
4. **Knockback** — короткий импульс игроку при ударе (и врагу при попадании мечом — приятный feedback).
5. **Game Over по HP=0** — переход в существующий `GameState.GAME_OVER` (экран уже есть в `src/ui/game_over.py`).

### Часть B. Дроп с врагов
6. **Pickup-сущность** (3 типа): `HeartPickup`, `CoinPickup`, `XPOrbPickup`.
7. **DropTable** — у каждого типа врага свои шансы и количество дропа (конфиг).
8. **PickupManager** — спавн, update (магнит к игроку в малом радиусе), сбор по коллизии, рендер.

### Часть C. Прогрессия
9. **Кошелёк** — `PlayerStats.coins: int`, +1 при пикапе монеты.
10. **Опыт и уровни** — `PlayerStats.xp`, `level`, `xp_to_next_level`. Формула: `xp_next = base * (level ** growth)`.
11. **Авто-прокачка** при наборе XP: `+max_health`, `+attack_damage_bonus`. Хил до полного при level-up (классика).
12. **HUD-расширение** — отображать монеты, текущий уровень, полоску XP.

### Что **не** входит (явно)
- Инвентарь, экипировка, магазины.
- Магия, скилы, дерево талантов.
- Сейв новых полей (coins/xp/level) — добавим в save-формат, но миграция старых сейвов не нужна (defaults).
- Спрайты пикапов — рисуем геометрией (красное сердце, жёлтый ромб монеты, голубой шар XP).
- Звуки.

---

## 🏗️ Архитектура (новые/изменённые модули)

```
src/entities/
├── enemy_ai.py          [+ ChaseBehavior]
├── pickup.py            [NEW] Pickup база + Heart/Coin/XPOrb
├── player_stats.py      [+ coins, xp, level, take_damage с i-frames, gain_xp, _level_up]
├── player_combat.py     [+ knockback на врагов при попадании]
└── player.py            [+ knockback самого игрока, мигание при i-frames]

src/systems/
├── enemy_manager.py     [+ apply_contact_damage(player, dt), drop_loot(enemy) при смерти]
├── pickup_manager.py    [NEW] спавн/update/draw/collect
└── progression.py       [NEW] чистые функции: xp_for_next_level(lvl), apply_level_up(stats)

src/ui/
└── hud.py               [+ draw_coins, draw_xp_bar, draw_level]

src/core/
├── config_loader.py     [+ валидация секций [combat], [pickups], [progression]]
└── game.py              [+ wiring PickupManager, проверка GAME_OVER при HP=0]
```

**Не трогаем:** `world/*`, `weapons.py`, `enemy_factory.py` (новый AI создаётся через ту же фабрику — параметризацией).

---

## ⚙️ Конфиг (новые секции `config.ini`)

```ini
[combat]
player_iframe_duration = 0.6        ; сек неуязвимости после удара
player_knockback_speed = 220        ; пикс/сек начальный импульс
player_knockback_duration = 0.15
enemy_knockback_speed = 180
enemy_knockback_duration = 0.12

[enemies]
; добавить к существующим:
light_touch_damage = 1
heavy_touch_damage = 2
fast_touch_damage = 1
light_chase_radius = 120            ; пикселей; 0 = не преследует
heavy_chase_radius = 100
fast_chase_radius = 180
chase_lose_radius = 280             ; за этим радиусом возврат к patrol

[pickups]
magnet_radius = 60                  ; в этом радиусе пикап летит к игроку
magnet_speed = 260
heart_heal_amount = 1
coin_value = 1
xp_orb_value = 5
lifetime = 30.0                     ; сек, потом исчезает

[drops]
; шансы 0..1 и количество "от-до"
light_heart_chance = 0.20
light_coin_chance = 0.60
light_coin_min = 1
light_coin_max = 2
light_xp_amount = 3
heavy_heart_chance = 0.50
heavy_coin_chance = 0.90
heavy_coin_min = 2
heavy_coin_max = 4
heavy_xp_amount = 10
fast_heart_chance = 0.10
fast_coin_chance = 0.50
fast_coin_min = 1
fast_coin_max = 2
fast_xp_amount = 5

[progression]
xp_base = 20                        ; XP до 2 уровня
xp_growth = 1.5                     ; xp_next = base * (level ** growth)
hp_per_level = 1                    ; +1 max HP за уровень
damage_per_level = 0                ; пока 0 — позже включим, сейчас только HP
heal_on_level_up = true
max_level = 20
```

> Все ключи валидируются в `ConfigLoader._validate_combat/_validate_pickups/_validate_drops/_validate_progression`. Шансы — в [0..1], числа — положительные, `max_level >= 1`.

---

## ✅ Чек-лист по этапам

### Этап 0 — Подготовка
- [x] Ветка `feature/combat-loop` от `dev`
- [x] Секции `[combat]`, `[pickups]`, `[drops]`, `[progression]` в `config.ini`
- [x] Валидация в `ConfigLoader` + тесты на ошибки конфига

### Этап 1 — ChaseBehavior
- [x] `ChaseBehavior(spawn_point, chase_radius, lose_radius, patrol_zone)` в `enemy_ai.py`
- [x] `update(enemy, dt, world, player)` — расширить сигнатуру AI чтобы получать `player` (обновить `IdleBehavior`/`PatrolBehavior` — игнорируют параметр)
- [x] Прокинуть `player` в `Enemy.update()` и `EnemyManager.update()`
- [x] Heavy/Fast получают `ChaseBehavior` по конфигу; Light остаётся на `PatrolBehavior` (или маленький радиус)
- [x] Тесты: входит в радиус → переключается на chase, выходит за `lose_radius` → возвращается, не пробивает стены (`world.check_collision`)

### Этап 2 — Контактный урон + i-frames + knockback
- [x] `PlayerStats.iframe_timer: float`, `take_damage(dmg)` уважает iframe и взводит таймер
- [x] `PlayerStats.update(dt)` — тикает iframe
- [x] `Player.knockback_vx/vy/timer` + применение в `update()` ДО handle_input (knockback приоритетнее ввода)
- [x] Мигание игрока при iframe (через skip кадра)
- [x] `EnemyManager.apply_contact_damage(player, dt)` — проверка коллизий + iframe + knockback
- [x] `Player.attack` — при попадании мечом задаёт врагу `knockback_vx/vy`
- [x] `Enemy.update()` — knockback двигает врага с проверкой коллизий
- [x] Тесты: i-frame блокирует двойной урон, knockback на врагов

### Этап 3 — Game Over
- [x] В `Game.update()`: `if player.is_dead() → state = GAME_OVER; game_stats.record_death()`
- [x] Сброс при «начать заново» из существующего экрана Game Over (уже работал)

### Этап 4 — Pickups
- [x] `pickup.py`: ABC `Pickup(x, y, lifetime)` + `HeartPickup`, `CoinPickup`, `XPOrbPickup`
- [x] `PickupManager`: `spawn(pickup)`, `update(dt, player)` (магнит + сбор + expire), `draw(screen, camera)`
- [x] Магнит + сбор по коллизии
- [x] Тесты: heart лечит, coin добавляет, xp маgнит/lifetime

### Этап 5 — Drops с врагов
- [x] `EnemyManager._drop_loot_from_dead(player)` + `_spawn_drops_for(enemy, player)` — адаптивный дроп
- [x] **Адаптивная логика:** HP < max → сердечки (по шансу); HP = max → монеты (по шансу); XP — всегда
- [x] Тесты: xp_always, hearts_when_hurt, coins_when_full_hp

### Этап 6 — Прогрессия
- [x] `PlayerStats`: `coins`, `xp`, `level`, `xp_to_next_level`, `gain_xp()`, `_level_up()`
- [x] `xp_for_next_level()` — чистая функция
- [x] `damage_bonus` учитывается в `Game.update()` (`weapon.damage + player.damage_bonus`)
- [x] Кап `max_level`
- [x] Тесты: формула XP, level-up, heal, max_level cap, coins

### Этап 7 — HUD
- [x] `HUD.draw_coins(screen, player)` — монеты
- [x] `HUD.draw_level_badge(screen, player)` — `Lv. N`
- [x] `HUD.draw_xp_bar(screen, player)` — полоска XP под HP

### Этап 8 — Save/Load
- [x] `SaveSystem` сохраняет `coins`, `xp`, `level`, `damage_bonus`
- [x] Загрузка старых сейвов — defaults (level=1, xp=0, coins=0)

### Этап 9 — Финал
- [x] `pytest tests/ -v --cov=src` — **183 passed, 75% coverage**
- [ ] Smoke-test (ручной запуск)
- [ ] PR в `dev`
- [ ] Удалить этот файл

---

## 🔢 Балансовые ориентиры (стартовые)

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| Стартовое max HP | 5 | Уже есть |
| Урон Heavy в контакт | 2 | Один промах = 40% HP — больно, но не фатально |
| i-frame | 0.6 с | Хватает выйти из хитбокса, не позволяет «застрять» |
| XP до 2 уровня | 20 | ≈ 4 Heavy или 7 Light |
| XP до 5 уровня | ≈ 87 | Заметная цель на первую сессию |
| Шанс сердечка с Heavy | 50% | Бои окупаются по HP |

---

## 🧪 Минимальный набор тестов для зелёного PR

- `tests/unit/test_enemy_ai.py::test_chase_enters_and_loses`
- `tests/unit/test_enemy_ai.py::test_chase_respects_world_collision`
- `tests/unit/test_player_stats.py::test_iframe_blocks_double_damage`
- `tests/unit/test_player_stats.py::test_gain_xp_levels_up_and_heals`
- `tests/unit/test_player_stats.py::test_max_level_cap`
- `tests/unit/test_player.py::test_knockback_overrides_input`
- `tests/unit/test_pickup.py::test_heart_does_not_overheal`
- `tests/unit/test_pickup.py::test_coin_increments_wallet`
- `tests/unit/test_pickup.py::test_xp_orb_grants_xp`
- `tests/unit/test_pickup_manager.py::test_magnet_pulls_within_radius`
- `tests/unit/test_pickup_manager.py::test_lifetime_expires`
- `tests/unit/test_enemy_manager.py::test_drop_spawns_on_death` (с фикс. seed)
- `tests/unit/test_progression.py::test_xp_curve_monotonic`
- `tests/unit/test_game.py::test_player_death_triggers_game_over`
- `tests/config/test_config_loader.py::test_validates_combat_pickups_drops_progression`

---

## 🚦 Порядок коммитов

1. `chore(config): add [combat]/[pickups]/[drops]/[progression] sections + validation`
2. `feat(ai): add ChaseBehavior strategy`
3. `feat(combat): contact damage with i-frames and knockback`
4. `feat(game): trigger game over on player death`
5. `feat(pickups): Heart/Coin/XPOrb + PickupManager with magnet`
6. `feat(enemies): drop loot table on death`
7. `feat(progression): coins, xp, levels with auto level-up`
8. `feat(hud): draw coins/level/xp bar`
9. `feat(save): persist coins/xp/level with backward defaults`
10. `docs: remove COMBAT_PROGRESSION_PLAN.md (after merge)`

---

**Готовность к старту:** да. Жду команды «погнали» — стартую с этапа 0.
