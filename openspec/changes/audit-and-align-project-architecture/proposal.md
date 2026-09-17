## Why

The project has evolved beyond its former documentation: it now includes a two-mission campaign, boss objectives, map transitions, mission result screens, armor, and expanded persistence, while architecture records were removed as obsolete and critical end-to-end behavior remains untested. A structured baseline is needed now to protect current gameplay, correct campaign/save defects, and establish scalable boundaries before adding quests, dialogue, more missions, maps, enemies, or content.

## What Changes

- Establish an evidence-based current-state architecture and a target architecture that keeps `Game` as a composition root while extracting scene routing, session lifecycle, combat resolution, persistence, and rendering responsibilities.
- Make campaign progression a first-class runtime contract, including deterministic mission completion, boss handling, map-local lifecycle, statistics, and transitions.
- Upgrade persistence so saves restore the actual map and campaign state atomically and reject invalid or partially applicable data.
- Define and enforce contracts for ASCII maps, overlays, symbols, dimensions, spawn points, and mission references.
- Restore concise authoritative project documentation generated from verified implementation rather than historical drafts.
- Replace brittle or misleading tests with characterization, unit, integration, and data-contract coverage for the current game.
- Add enforceable formatting, linting, type-checking, coverage, cross-platform, and repository-cleanliness quality gates using the project's existing toolchain.
- Remove or explicitly isolate unwired placeholders, stale configuration paths, duplicated load logic, and hidden global/runtime side effects.
- Preserve current player-facing mechanics unless a corrective requirement below explicitly changes defective behavior.

## Capabilities

### New Capabilities

- `campaign-lifecycle`: Defines mission start, objective completion, boss resolution, map transitions, map-local state replacement, and campaign completion behavior.
- `persistence-integrity`: Defines complete, versioned, atomic save/load behavior for player, world, campaign, map-local runtime, and backward compatibility.
- `map-data-contract`: Defines validation and loading requirements for map layers, dimensions, symbols, spawn points, and mission-to-map consistency.
- `engineering-governance`: Defines the authoritative architecture/documentation set and automated quality gates that keep code, tests, data, and documentation aligned.

### Modified Capabilities

None. This repository has no existing OpenSpec capability specifications.

## Impact

- Core orchestration and state flow: `src/core/game.py`, `src/core/game_states.py`, `src/core/game_stats.py`.
- Campaign and presentation: `src/systems/mission.py`, `src/ui/mission_screens.py`, `src/ui/map_transition.py`.
- Persistence and runtime managers: `src/systems/save_system.py`, enemy/projectile/pickup managers.
- World/content/configuration: `src/world/`, `data/`, `config.ini`, and configuration loading.
- Tests and automation: `tests/`, `.github/workflows/`, and existing Black/Flake8/mypy/pytest tooling.
- Documentation: a new minimal authoritative README, architecture/design guide, testing guide, and generated OpenSpec capability baseline; deleted historical drafts remain deleted unless selectively recovered as clearly marked history.
- Save compatibility requires an explicit schema migration. Invalid or internally inconsistent saves may be rejected where they were previously partially applied.
