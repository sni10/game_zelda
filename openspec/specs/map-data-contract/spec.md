# Map Data Contract Specification

## Purpose

Defines fail-fast map and mission data contracts so authored content is structurally valid, dimensionally consistent, and safe to load in gameplay.

## Requirements

### Requirement: Map layers are structurally valid
The system SHALL require each map layer to be rectangular, non-empty, composed only of registered symbols, and dimensionally compatible with every associated layer.

#### Scenario: Overlay dimensions differ from ground
- **WHEN** an overlay has a different row count or width from its ground map
- **THEN** validation fails and identifies the incompatible layer

#### Scenario: Unknown symbol is present
- **WHEN** a map contains an unregistered symbol
- **THEN** validation fails at the symbol location instead of silently treating it as empty terrain

### Requirement: Playable maps have one valid player spawn
The system SHALL require exactly one player spawn on every directly playable mission map.

#### Scenario: Spawn is missing or duplicated
- **WHEN** a playable map has zero or multiple player spawn markers
- **THEN** validation fails before gameplay starts

### Requirement: Runtime dimensions derive from map data
The system SHALL derive map pixel dimensions from validated rows, columns, and tile size, and SHALL reject contradictory manually supplied dimensions.

#### Scenario: Mission dimensions disagree with map dimensions
- **WHEN** mission metadata declares dimensions inconsistent with its validated map
- **THEN** content validation fails with both expected and declared dimensions

### Requirement: Mission content references are valid
The system SHALL validate that every mission map exists and can satisfy its required spawn, objective, and reachability constraints.

#### Scenario: Required objective target has no reachable position
- **WHEN** no reachable location can host a required target
- **THEN** mission validation fails rather than allowing automatic completion

### Requirement: Content contracts run independently
The system SHALL provide a non-interactive validation command that checks all shipped maps and mission definitions without launching the game.

#### Scenario: Continuous integration validates content
- **WHEN** repository quality checks run
- **THEN** malformed or inconsistent map and mission data causes a failing result
