# Campaign Lifecycle Specification

## Purpose

Defines deterministic campaign and mission behavior so progression remains correct as maps, objectives, bosses, and presentation flows expand.

## Requirements

### Requirement: Mission activation is complete or fails explicitly
The system SHALL activate a mission only after its map, player spawn, required objective targets, and map-local runtime have been created successfully. A failed required spawn MUST NOT satisfy its objective.

#### Scenario: Required boss cannot be spawned
- **WHEN** a mission requires a boss and no valid spawn position can be produced
- **THEN** mission activation fails with a visible diagnostic and the mission remains incomplete

#### Scenario: Mission starts successfully
- **WHEN** all required mission resources and objective targets are valid
- **THEN** the mission enters active play with its objective unsatisfied

### Requirement: Mission completion is resolved exactly once
The system SHALL complete a mission only after its objective is satisfied and all effects of the completing action, including defeat accounting and loot generation, have been resolved.

#### Scenario: Boss is defeated
- **WHEN** the active mission boss is reduced to zero health
- **THEN** defeat statistics and loot are resolved before the mission-complete state is entered exactly once

### Requirement: Mission transition preserves run state
The system SHALL preserve run-scoped player progression, equipment, ammunition, and cumulative statistics while replacing all map-scoped state during a mission transition.

#### Scenario: Player advances to the next mission
- **WHEN** the player confirms continuation from a completed non-final mission
- **THEN** the next map starts with preserved run state and without enemies, projectiles, or pickups from the previous map

### Requirement: Campaign completion is terminal
The system SHALL enter a campaign-complete state after the final mission and SHALL NOT attempt to activate a nonexistent next mission.

#### Scenario: Final mission is completed
- **WHEN** the final mission objective has been resolved
- **THEN** the campaign-complete presentation shows the final cumulative statistics

### Requirement: Campaign statistics have stable semantics
The system SHALL count attacks, damage, healing, collected items, travel distance, and active play time according to documented event semantics and SHALL exclude map teleports and paused/menu time.

#### Scenario: Mission transition teleports the player
- **WHEN** the player position changes because a new mission map is activated
- **THEN** the teleport distance is not added to traveled distance
