# Zelda-like Game

[![English](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![Русский](https://img.shields.io/badge/lang-ru-blue.svg)](README_RU.md)

[![Release](https://img.shields.io/github/v/release/sni10/game_zelda?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sni10/game_zelda/releases)
[![Tests](https://img.shields.io/github/actions/workflow/status/sni10/game_zelda/python-tests.yml?style=for-the-badge&logo=github-actions&logoColor=white&label=Tests)](https://github.com/sni10/game_zelda/actions/workflows/python-tests.yml)
[![Coverage](https://img.shields.io/badge/Coverage-73%25-brightgreen?style=for-the-badge&logo=python&logoColor=white)](https://github.com/sni10/game_zelda)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.6+-green?style=for-the-badge&logo=python&logoColor=white)](https://pygame.org)
[![License](https://img.shields.io/github/license/sni10/game_zelda?style=for-the-badge&color=blue)](LICENSE)

A base implementation of a 2D Zelda-style game using Python and Pygame.

## Features

### ✅ Implemented Functions

#### 🎮 Game Systems
- **Main Menu**: Full-featured menu with navigation and dynamic options.
- **State System**: MENU, PLAYING, GAME_OVER with smooth transitions.
- **Game Over Screen**: Informative death screen with statistics.

#### 👤 Character and Health
- **Movement**: 8-way movement (including diagonals) with proper speed normalization.
- **Health System**: 100 HP with a visual health bar.
- **Player Death**: Automatic transition to Game Over at 0 HP.
- **Attack**: Attack system with cooldown and visual direction indication.

#### 🌍 World and Terrain
- **Large World**: 2000x2000 pixel game map.
- **Terrain System**: 6 types of terrain with different properties.
- **Terrain Damage**: Swamps and sands deal damage to the player.
- **Speed Modification**: Certain terrain types slow down movement.
- **Map Loading**: Support for ASCII maps from files.

#### 💾 Saves and Statistics
- **Quick Saves**: F5 for saving, F9 for loading.
- **JSON Format**: Structured saves with versioning.
- **Game Statistics**: Play time, damage, items collected, distance traveled.
- **Automatic Tracking**: All actions are recorded in statistics.

#### 🖥️ Interface
- **Camera**: Smoothly follows the player with world boundary constraints.
- **Collisions**: Collision system with obstacles and terrain.
- **Mini-map**: Displays player position and visibility area.
- **Debug**: F1 to toggle debug information.

### 🎮 Controls

#### In Menu:
- **Up/Down Arrows** - Navigate menu items.
- **Enter** - Select menu item.
- **ESC** - Exit game.

#### In Game:
- **WASD** or **Arrows** - Movement in 8 directions.
- **Space** - Attack in the looking direction.
- **F1** - Toggle debug information.
- **F5** - Quick save.
- **F9** - Quick load.
- **ESC** - Return to main menu.

#### On Game Over Screen:
- **WASD/Arrows** - Navigate options.
- **Enter/Space** - Select option.

### 🏗️ Architecture
The project follows OOP, SOLID, and DRY principles with a modular structure:

```
game_zelda/
├── README.md
├── main.py                    # Entry point
├── config.ini                # Configuration file
├── src/                       # Source code
│   ├── core/                  # Core game systems
│   │   ├── game.py           # Main Game class with game loop
│   │   ├── config_loader.py  # Config loading system
│   │   ├── game_states.py    # Game state enum
│   │   └── game_stats.py     # Statistics tracking system
│   ├── entities/             # Game entities
│   │   ├── player.py         # Player class with movement, attack, and health
│   │   ├── enemy.py          # Enemy classes
│   │   ├── item.py           # Item classes
│   │   └── npc.py            # NPC classes
│   ├── world/                # World and environment
│   │   ├── world.py          # World class with map and camera
│   │   └── terrain.py        # Terrain and damage system
│   ├── ui/                   # User interface
│   │   ├── menu.py           # Main menu
│   │   └── game_over.py      # Game Over screen
│   ├── systems/              # Game systems
│   │   └── save_system.py    # Save/load system
│   └── utils/                # Utilities
│       └── debug.py          # Debug functions
├── data/                     # Game data
│   ├── main_world.txt        # ASCII map of the main world
│   ├── cave_world.txt        # ASCII map of the cave world
│   └── underground_world.txt # ASCII map of the underground world
├── saves/                    # Saves folder
│   └── quicksave.json        # Quick save file
├── docs/                     # Documentation
│   ├── release-notes/        # Release notes
│   ├── game-structure-map.md # Game structure map
│   └── implementation-plan.md # Implementation plan
└── tests/                    # Tests
    ├── unit/                 # Unit tests
    └── config/               # Configuration tests
```

### 🎨 Visual Elements
Simple geometric shapes are used instead of textures:

#### Player and Interface
- **Player**: Green rectangle (red during attack).
- **Looking Direction**: White dot on the player.
- **Attack**: Yellow area in the looking direction.
- **Health Bar**: Red-green gradient at the top of the screen.

#### Terrain
- **Void**: Dark green background.
- **Mountains**: Dark gray blocks (impassable).
- **Water**: Blue blocks (impassable).
- **Trees**: Dark green blocks (decorative).
- **Swamps**: Brown-green blocks (damage).
- **Sands**: Sand-colored blocks (damage + slowdown).

#### Interface
- **Mini-map**: Top right corner with player and obstacle dots.
- **Menu**: Stylized with yellow highlighting and arrows.
- **Game Over**: Semi-transparent overlay with a red header.

## 🌿 Branching Strategy

Game Zelda follows the **GitFlow** workflow:

- **`main`** – production-ready code.
- **`stage`** – pre-production.
- **`dev`** – integration branch for new features.
- **`feature/*`** – new functionality based on dev.
- **`release/*`** – release preparation based on stage.
- **`hotfix/*`** – urgent fixes based on main.

### Workflow process:
```
feature/*   -> dev
dev         -> stage
stage       -> release/*
release/*   -> main + dev
hotfix/*    -> main + dev
```

### Development Process:
1. 🔧 **Develop features** in `feature/*` branches.
2. 🔄 **Merge to `dev`** for integration.
3. 📤 **Merge from `dev` to `stage`** for testing.
4. 📸 **Take a snapshot release** from `stage` to `release/*` branches.
5. 🚀 **Release with features** merged into `main`, `dev`, and `stage`.

## 🔖 Versioning

Releases are created automatically upon pushing to `stage`. The workflow analyzes commits and increments the major, minor, or patch version accordingly, tagging the repository `vX.Y.Z` and generating release notes.

### Semantic Versioning:
- **MAJOR** (X.0.0) - breaking changes.
- **MINOR** (0.X.0) - new functionality, backward compatible.
- **PATCH** (0.0.X) - bug fixes, backward compatible.

## Running the Game

```bash
python main.py
```

The main entry point is located in the project root for convenience.

## Technical Specifications

- **Window Size**: 1024x768 pixels.
- **World Size**: 2000x2000 pixels.
- **FPS**: 60 frames per second.
- **Player Speed**: 120 pixels per second (as in classic Zelda).
- **Tile Size**: 32x32 pixels.

## Future Extensions

The architecture is prepared for adding:
- **Enemies** (Enemy class)
- **Items and Inventory** (Item class)
- **NPCs and Dialogues** (NPC class)
- **Sound Effects and Music**
- **Save/Load Systems**
- **Additional Levels and Locations**
- **Magic and Spells**

## Requirements

- Python 3.7+
- Pygame 2.0+

## Dependency Installation

```bash
pip install pygame
```

## 📚 Documentation

### 📋 Release Notes
All release notes are available in the documentation folder:
- [Release Notes v0.0.1](docs/release-notes/release_notes_v0.0.1.md) - First release.
- [Release Notes v0.1.1](docs/release-notes/release_notes_v0.1.1.md) - Test fixes and CI/CD.
- [Release Notes v0.2.1](docs/release-notes/release_notes_v0.2.1.md) - Comprehensive update of game systems.

---

### 🔧 Workflow Files Explanation

## 1. 🧪 **python-tests.yml** - Code Testing

### What it does:
- **Runs Python tests** on every push or PR to `main`, `dev`, `stage` branches.
- **Checks code quality** before merging changes.
- **Generates coverage reports**.

### Triggers:
```yaml
on:
  push:
    branches: [ main, dev, stage ]
  pull_request:
    branches: [ main, dev, stage ]
```

### Process:
1. ✅ **Code Checkout** - downloads code from repository.
2. ✅ **Set up Python 3.10** - configures the environment.
3. ✅ **Install dependencies** - `pip install -r requirements.txt`.
4. ✅ **Run tests** - `pytest` with code coverage.
5. ✅ **Upload reports** - sends results to Codecov.

**Goal:** Ensure code works correctly before merging.

---

## 2. 🔄 **auto-sync-branches.yml** - Automatic Branch Synchronization

### What it does:
- **Automatically creates PRs** for branch synchronization following GitFlow.
- **Maintains the correct flow**: `dev → stage → main`.
- **Creates sync branches** for safe merging.

### Triggers:
```yaml
on:
  push:
    branches: [dev, stage]
```

### Logic:

#### On push to **dev**:
1. ✅ Checks for new commits in `dev` compared to `stage`.
2. ✅ Creates branch `auto-sync/dev-to-stage-YYYYMMDD-HHMMSS`.
3. ✅ Creates PR: **dev → stage**.

#### On push to **stage**:
1. ✅ Checks for new commits in `stage` compared to `main`.
2. ✅ Creates branch `auto-sync/stage-to-main-YYYYMMDD-HHMMSS`.
3. ✅ Creates PR: **stage → main**.

### In PR:
- 📋 **Title**: "🔄 Auto-sync dev → stage" or "🔄 Auto-sync stage → main".
- 📋 **Description**: List of changes (up to 10 commits).
- 📋 **Automatic creation**: No manual intervention required.

**Goal:** Automate the GitFlow development process.

---

## 3. 🏷️ **versioning.yml** - Automatic Release Creation

### What it does:
- **Automatically creates new versions** upon merging to `main`.
- **Generates changelog** describing the changes.
- **Creates Git tags and GitHub releases**.
- **Uses Semantic Versioning** (major.minor.patch).

### Triggers:
```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

### Versioning Logic:

#### Automatic version type detection:
- 🔴 **Major** (3.0.0): If "BREAKING CHANGE" is in commits.
- 🟡 **Minor** (0.1.0): If "feat:" is in commits.
- 🟢 **Patch** (0.0.1): All other changes.

#### Created artifacts:
1. ✅ **New tag**: `v0.1.0`, `v0.2.0`, etc.
2. ✅ **GitHub Release** with description:
    - 📊 Statistics (commit count, contributors).
    - 📋 Changelog (list of changes).
    - 🔗 Links to diff and commits.
3. ✅ **Automatic tag push** to repository.

**Goal:** Automate the release process and changelog maintenance.

---

## 🔄 How everything works together:

### Full Development Cycle:

1. **Feature Development** → Push to `dev`.
    - ✅ `python-tests.yml` checks the code.
    - ✅ `auto-sync-branches.yml` creates PR `dev → stage`.

2. **Testing** → Merge PR to `stage`.
    - ✅ `python-tests.yml` checks the code.
    - ✅ `auto-sync-branches.yml` creates PR `stage → main`.

3. **Release** → Merge PR to `main`.
    - ✅ `python-tests.yml` checks the code.
    - ✅ `versioning.yml` creates a new release.

### 🎯 Result:
- ✅ **High-quality code** (tests at every stage).
- ✅ **Automated GitFlow** (dev → stage → main).
- ✅ **Automatic releases** with changelog.
- ✅ **Minimal manual work** (only PR approval).

**All three workflows work synchronously to ensure a high-quality and automated development process!** 🚀

---

**Built using OOP, SOLID, and DRY principles for scalability and extensibility.**