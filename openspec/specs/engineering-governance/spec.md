# Engineering Governance Specification

## Purpose

Defines the maintained project knowledge and automated quality controls required to keep implementation, tests, content, and contributor guidance aligned.

## Requirements

### Requirement: Documentation has explicit authority
The repository SHALL maintain one player-facing overview, one contributor guide, one current architecture document, and capability specifications. Historical or speculative material MUST be clearly separated from current behavior.

#### Scenario: Contributor looks up current architecture
- **WHEN** a contributor follows repository documentation links
- **THEN** they reach a single current architecture description that matches executable module boundaries

### Requirement: Current capabilities are documented from evidence
Documentation SHALL distinguish implemented behavior, accepted near-term design, backlog ideas, and historical records, and SHALL include campaign, mission, map transition, armor, and save behavior that exists in the shipped code.

#### Scenario: Planned feature is not implemented
- **WHEN** a design idea has no active runtime integration
- **THEN** documentation labels it as proposed or deferred rather than current functionality

### Requirement: Automated checks enforce repository quality
Continuous integration SHALL run formatting verification, linting, tests with branch coverage, map-data validation, and repository-cleanliness checks on supported environments.

#### Scenario: Test writes an untracked repository file
- **WHEN** the automated test suite leaves generated files in the worktree
- **THEN** the quality workflow fails

#### Scenario: Critical flow lacks required coverage
- **WHEN** coverage falls below the recorded baseline or critical campaign and persistence modules fall below their configured thresholds
- **THEN** the quality workflow fails

### Requirement: Tests are isolated and behavior-focused
Automated tests SHALL use temporary storage, deterministic clocks or timestamps, centralized headless graphics fixtures, and public behavioral contracts wherever practical.

#### Scenario: Test suite runs on a clean machine
- **WHEN** tests execute on any supported operating system without developer-specific paths
- **THEN** they pass without reading or writing locations outside managed temporary directories

### Requirement: Architecture boundaries are reviewable
The project SHALL document allowed dependency directions and SHALL provide automated checks for high-value boundaries where accidental imports or global side effects would compromise isolation.

#### Scenario: Presentation accesses persistence directly
- **WHEN** a prohibited dependency crosses a documented boundary
- **THEN** an automated architecture check reports the violation
