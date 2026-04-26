# AGENTS.md - AI Coding Agent Guide for Zelda Game Codebase

This file provides essential knowledge for AI coding agents to be immediately productive in this 2D Zelda-style game codebase.

## 🏗️ Architecture Overview

### Core Design: ECS + Legacy Hybrid Pattern
The game uses an **Entity-Component-System (ECS)** architecture for multi-world support, **while maintaining legacy Player/World objects for backward compatibility**:

- **ECS Layer** (`src/core/ecs/`): Modern system for multi-world management, Z-levels, portals
- **Legacy Layer**: Classic `Player` and `World` classes kept for compatibility and immediate rendering
- **Sync Mechanism**: `game.sync_player_position()` keeps ECS and legacy systems in sync bidirectionally

**Why this matters**: When modifying game state, you must update BOTH systems:
```python
# After changing player position:
player_pos.set_position(self.player.x, self.player.y)  # Update ECS from legacy
self.player.x = player_pos.x  # Update legacy from ECS if needed
```

### Multi-World System with Z-Levels
Three concurrent worlds exist at once:
- **"main_world"** (2000x2000): Surface level
- **"cave_world"** (800x600): Tunnels accessible via Z-transitions  
- **"underground_world"** (600x400): Deep tunnels

Worlds are managed by `WorldManager` which:
1. Maintains `WorldState` for each world (loaded entities, last player position)
2. Tracks active world in `current_world_id`
3. Caches max 3 loaded worlds in memory for performance
4. Handles Z-transitions (E key) and portals (P key) via `ZTransitionSystem` and `PortalSystem`

**Critical pattern**: Player transitions trigger:
```
1. Z/Portal System processes transition
2. PositionComponent updated with new world_id/z_level
3. sync_player_position() called
4. Legacy World object recreated/cached via _get_or_create_legacy_world()
5. LayerRenderer or legacy renderer activated based on Z-level
```

## 📋 Configuration-First Architecture

### ConfigLoader Pattern (`src/core/config_loader.py`)
All game parameters are externalized in `config.ini` and validated at startup:
- Validation occurs in `ConfigLoader.load_config()` - throws `ConfigValidationError` if invalid
- Use singleton functions: `get_config(key)` and `get_color(color_name)`
- Config sections: display, world, player, attack, colors, debug, world_generation

**Never hardcode magic numbers** - Example wrong ❌:
```python
health -= 10  # Wrong!
```

**Always use config** - Example right ✅:
```python
player_speed = get_config('PLAYER_SPEED')
health -= damage_amount  # Configure damage in config
```

## 🎮 Entity-Component-System Details

### Component-Based Architecture
All game objects composed of components attached to `Entity`:

```python
# Creating a new entity
entity = entity_manager.create_entity()
entity.add_component(PositionComponent(x, y, z, world_id))
entity.add_component(RenderLayerComponent(layer_priority))
entity.add_component(ZLevelComponent(z))
```

**Key components** (`src/core/ecs/component.py`):
- `PositionComponent(x, y, z, world_id)`: Location with Z-level
- `RenderLayerComponent(priority)`: Render order
- `ZLevelComponent(z)`: Current depth level
- `PortalComponent`: Portal destination data
- `WorldComponent`: World membership

**Pattern**: Query entities by components:
```python
if entity.has_components(PositionComponent, RenderLayerComponent):
    render_system.process(entity)
```

### System Execution Order
Systems update sequentially via `SystemManager.update_all(dt)`:
1. **ZTransitionSystem**: Handles Z-level changes
2. **PortalSystem**: Handles world transitions
3. **LayerRenderer**: Renders entities to screen

Systems registered in `game.start_new_game()` - add new systems here.

## 🎨 Rendering Strategy

### Z-Level Dependent Rendering
Rendering **changes based on player's Z-level**:

**Surface (Z=0)**: Uses legacy `World.draw()` with camera
```python
if not player_pos or player_pos.z == 0:
    self.world.draw(self.screen, self.player.x, self.player.y)
```

**Underground (Z=-1)**: Uses `LayerRenderer` for multi-layered caves
```python
else:  # Z == -1
    self.layer_renderer.update(dt)
    # Renders with layer strategies
```

**Why two renderers?** Legacy World.draw() is simple/fast for surface. LayerRenderer supports complex Z-stacking for caves.

### Layer Rendering Strategy Pattern (`src/rendering/layer_strategies.py`)
Different rendering strategies for different Z-levels via `StrategyFactory`:
- `create_strategy(z_level)`: Returns appropriate renderer for depth
- Strategies handle visual effects (darkness underground, fog in caves)

## 💾 Save/Load System

### Two-Tier Save System
1. **Legacy SaveSystem** (`src/systems/save_system.py`): Saves Player + World state to JSON
2. **MultiWorldSaveSystem** (`src/systems/multiworld_save_system.py`): Saves entire ECS + WorldManager state

**Current behavior**: 
- F5 quicksaves using legacy system
- Modern system ready for future implementation

**Compatibility check in `quickload()`**:
```python
if not self.player or not self.world:
    # Create empty World/Player before applying save
    self.world = World(...)
    self.player = Player(0, 0)
```

## 🔄 Data Flow: Game Loop

Every frame (60 FPS target):

```
handle_events() (input/menus)
  ↓
update(dt) 
  ├─ Player.handle_input(keys)
  ├─ Player.update(dt, world, stats)
  ├─ sync_player_position()  ⚡ CRITICAL
  ├─ WorldManager.update(dt)
  └─ SystemManager.update_all(dt)
  ↓
draw()
  ├─ If Z==0: World.draw() + Player.draw()
  └─ If Z==-1: LayerRenderer.update()
```

**Timing constraint**: `dt` capped at 1/30s for physics stability: `dt = min(dt, 1.0/30.0)`

## ⚡ Critical Integration Points

### 1. Adding New Game Objects
Must touch BOTH systems:
```python
# Legacy
world.obstacles.append(pygame.Rect(...))

# ECS
entity = entity_manager.create_entity()
entity.add_component(PositionComponent(x, y, 0, "main_world"))

# Keep synced
entity_world_cache[entity.id] = "main_world"
```

### 2. World Transitions (Player moves between worlds)
Sequence in `WorldManager.switch_to_world()`:
1. Save current world state (player position via `world_state.set_player_position()`)
2. Load target world (create if needed)
3. Update player PositionComponent with new world_id
4. Call `game.sync_player_position()` to update legacy objects

### 3. Collision Detection
Only legacyPlayer/World collision works:
```python
# Player.update() calls this:
if world.check_collision(self.rect):
    self.x = old_x
    self.y = old_y  # Undo movement
```

ECS entities don't have collision logic yet - future feature.

## 📊 Logging & Statistics

### Game Session Logging
Every run creates timestamped log in `logs/game_session_YYYYMMDD_HHMMSS.log`:
- `game.log(message, level="INFO")` writes to file + console (INFO/WARNING/ERROR levels)
- Used for debugging multi-world transitions and world switching

### Game Statistics (`src/core/game_stats.py`)
Tracks player progression:
- `update_position(x, y)`: Maps traveled distance
- `record_death()`: Death counter
- `update_stat(key, value)`: Custom metrics

Access via `game.game_stats` - required for Game Over screen.

## 🧪 Testing Requirements

### Test Structure
- **Unit tests**: `tests/unit/` - test individual components
- **Config tests**: `tests/config/` - test ConfigLoader validation

### Pre-Commit Checklist
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Check specific test
pytest tests/unit/test_player.py::TestPlayer::test_movement -v

# Code quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

**Coverage requirement**: Maintain 70%+ (currently 73%)

### Mocking Patterns
- Use `pytest-mock` to mock pygame/file operations
- Tests should not create actual game windows: use `@patch` decorator
- Config validation tests use fresh ConfigParser instances

## 🚀 Adding Features: Workflow

### 1. New Game Mechanic (e.g., new terrain type)
1. Add config in `config.ini` under appropriate section
2. Validate in `ConfigLoader._validate_*()` method
3. Use `get_config()` in implementation
4. Add unit test in `tests/unit/`
5. Create PR to `dev` branch

### 2. New World/Map
1. Create ASCII map file in `data/<world_id>.txt` — **только** ASCII-сетка тайлов, никаких комментариев и текста
2. (Опц.) Создать `data/<world_id>_overlay.txt` — верхний визуальный слой (Z=2), рисуемый поверх игрока с полупрозрачностью когда игрок под тайлом. Парсер автоматически найдёт этот файл рядом с основной картой.
3. Register in `WorldManager.create_world()` call in `game.start_new_game()`
4. Add factory method in `src/factories/world_factory.py`
5. Test transition via E/P keys

**Принципы карт:**
- **Один слой = один файл.** Не лепить overlay в тот же файл через маркеры.
- **Чистый ASCII.** Никаких `# комментариев` в файлах карт — пояснения только в AGENTS.md / коде.
- **Overlay >= ground footprint.** Overlay-крыша должна быть на 1 тайл шире земляного следа холма со всех сторон, иначе игрок вылезет в "дырку" по углам.
- **HILL_SURFACE (`H`)** на земле = непроходимая стенка холма. На overlay = чисто визуальная крыша (без коллизий, с полупрозрачностью когда игрок под ней).

### 3. New Rendering Feature
1. Add strategy in `src/rendering/layer_strategies.py` if Z-level dependent
2. Otherwise modify `World.draw()` or legacy rendering
3. Test in both Z=0 and Z=-1 modes

## 📍 File Navigation Quick Reference

| Purpose | File(s) |
|---------|---------|
| Main loop, state transitions | `src/core/game.py` |
| Configuration validation | `src/core/config_loader.py` |
| Player movement/attack | `src/entities/player.py` |
| ECS entity/component management | `src/core/ecs/{entity,component,system}.py` |
| Multi-world management | `src/world/world_manager.py` |
| Rendering (Z-level aware) | `src/rendering/layer_renderer.py` |
| Save/load data | `src/systems/save_system.py` |
| Debug display | `src/utils/debug.py` |
| Terrain data | `src/world/terrain.py` |
| UI (menus, HUD) | `src/ui/{menu,game_over}.py` |

## 🎯 Common Pitfalls & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Player position desynchronized | ECS updated but legacy not synced | Call `game.sync_player_position()` |
| Rendering glitches on Z=0 | Using LayerRenderer instead of World.draw() | Check `player_pos.z == 0` condition |
| Config not loading | File not in project root | Verify `config.ini` exists in `/` |
| Collision fails | Only legacy collision implemented | Don't use ECS for collision yet |
| World not switching | WorldManager not created/registered | Ensure in `game.start_new_game()` sequence |

## 🔌 External Dependencies

- **pygame 2.5+**: Rendering, input, clock
- **configparser**: INI file parsing (stdlib)
- **json**: Save file format (stdlib)
- **pytest/pytest-cov**: Testing (dev-only)
- **black/flake8/mypy**: Code quality (dev-only)

No special build steps - pure Python. Run `pip install -r requirements.txt`.

## 📚 Branch Strategy for Agents

- **Feature development** → Create PR against `dev` branch
- **Tests must pass** before merging (CI/CD enforces)
- **No direct commits to main** - GitFlow only
- **Semantic versioning** applied automatically to releases

---

**Last Updated**: 2026-04-26
**Target Python**: 3.10+
**Game Version**: 0.2.1+

