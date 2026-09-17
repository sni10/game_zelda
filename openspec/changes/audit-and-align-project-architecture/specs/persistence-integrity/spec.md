## Purpose

Defines reliable, versioned save and load behavior that restores a complete playable run without mixing state from different maps or campaigns.

## ADDED Requirements

### Requirement: Saves identify the complete run state
The system SHALL persist the active campaign and mission identity, actual map identity, objective progress, campaign statistics snapshots, player state, and all required map-local runtime state.

#### Scenario: Save during a later mission
- **WHEN** the player saves after advancing beyond the first mission
- **THEN** the save identifies that exact mission and map rather than a global default map

### Requirement: Loading is atomic
The system SHALL validate and construct the complete target run before replacing the active run. A load failure MUST leave the current run unchanged.

#### Scenario: Save contains invalid aggregate data
- **WHEN** any required campaign, map, player, or runtime component cannot be validated or constructed
- **THEN** loading fails with a visible error and no partial state is applied

### Requirement: Save writes are crash-safe
The system SHALL write save data to a temporary file and atomically replace the target only after serialization succeeds.

#### Scenario: Serialization or write fails
- **WHEN** a save cannot be fully written
- **THEN** the previously valid target save remains readable

### Requirement: Save versions have explicit migrations
The system SHALL migrate every supported historical save version through explicit, tested version steps and SHALL reject unsupported versions without partial application.

#### Scenario: Supported legacy save is loaded
- **WHEN** a valid save from a supported older schema is selected
- **THEN** it is migrated to the current in-memory schema and restored successfully

#### Scenario: Unsupported future save is loaded
- **WHEN** a save declares a schema version newer than the running game supports
- **THEN** loading is rejected with a compatibility message

### Requirement: Saved identifiers are stable
The system SHALL serialize stable catalog identifiers for maps, enemies, weapons, armor, and objectives rather than localized or display names.

#### Scenario: Display name changes
- **WHEN** a display label changes between releases
- **THEN** an existing save still resolves the same catalog entity

