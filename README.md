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
- **Movement**: Free-angle movement relative to where you're aiming.
- **Health System**: HP with a visual health bar.
- **Player Death**: Automatic transition to Game Over at 0 HP.
- **Combat**: Melee and ranged weapons with cooldowns and ammo/reload.

#### 🌍 World and Terrain
- **Large World**: 2000x2000 pixel game map.
- **Terrain System**: Several types of terrain with different properties.
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
- **Inventory**: Weapon slots screen with drag-and-drop.
- **Debug**: F1 to toggle debug information.

### 🎮 Controls

#### In Menu:
- **Up/Down Arrows** - Navigate menu items.
- **Enter** - Select menu item.
- **ESC** - Exit game.

#### In Game:
- **Mouse** - Aim (360°); the player always faces the cursor.
- **WASD** - Move relative to where you're aiming: **W** forward, **S** backward, **A/D** strafe left/right.
- **Space** or **Left Click** - Attack/fire in the aim direction.
- **Shift** - Sprint.
- **1-8** - Select weapon slot.
- **R** or **Right Click** - Reload.
- **I** - Open inventory.
- **F1** - Toggle debug information.
- **F5** - Quick save.
- **F9** - Quick load.
- **ESC** - Return to main menu.

#### On Game Over Screen:
- **WASD/Arrows** - Navigate options.
- **Enter/Space** - Select option.

### 🎨 Visual Elements
Simple geometric shapes are used instead of textures:

#### Player and Interface
- **Player**: Green rectangle (red during attack).
- **Looking Direction**: White dot on the player.
- **Attack**: Colored area in the aim direction (color depends on the equipped weapon).
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

## Running the Game

```bash
python main.py
```

The main entry point is located in the project root for convenience.

## Requirements

- Python 3.7+
- Pygame 2.0+

## Dependency Installation

```bash
pip install pygame
```

## Future Extensions

The architecture is prepared for adding:
- **NPCs and Dialogues**
- **Sound Effects and Music**
- **Additional Levels and Locations**
- **Magic and Spells**
- **Armor and a full item inventory**

## 📚 Documentation

### 📋 Release Notes
All release notes are available in the documentation folder:
- [Release Notes v0.0.1](docs/release-notes/release_notes_v0.0.1.md) - First release.
- [Release Notes v0.1.1](docs/release-notes/release_notes_v0.1.1.md) - Test fixes and CI/CD.
- [Release Notes v0.2.1](docs/release-notes/release_notes_v0.2.1.md) - Comprehensive update of game systems.
- [Release Notes v0.3.0](docs/release-notes/release_notes_v0.3.0.md) - Save system and progression.

---

**Built using OOP, SOLID, and DRY principles for scalability and extensibility.**

*Looking for architecture, branching/CI-CD, and other developer-facing details? See [CLAUDE.md](CLAUDE.md).*
