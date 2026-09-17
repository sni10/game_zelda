## Context

See `proposal.md` for motivation and the capability specs for behavioral contracts.

The current implementation is a single-threaded Pygame application with a central `Game` object. Its loop is conventional and clear (`events -> update -> draw`), but `Game` also acts as composition root, state router, campaign service, combat coordinator, persistence controller, autosave scheduler, and render coordinator. The project uses pragmatic object composition rather than an ECS.

Patterns already working well:

- Strategy-like abstractions for weapons, enemy AI, and mission objectives.
- Catalog/factory creation for weapons, armor, and enemy types.
- Composition for player stats/combat and world/camera.
- UI actions returned to the central coordinator instead of most screens mutating domain state.
- Grid indexes and reachability checks for terrain and spawn logic.

The newest campaign flow is only partially integrated. Two missions are hard-coded in Python; only boss-defeat objectives exist; mission dimensions duplicate map data; the save schema does not persist campaign progress; map loading silently accepts missing files and unknown symbols; and mission transitions preserve map-local pickups. `Game` checks objective completion before all consequences of a killing action have been finalized.

The dominant constraints are:

- Preserve current player-facing mechanics while fixing demonstrably incorrect state handling.
- Keep one active world at a time; multi-world, portals, Z-levels, ECS, and network services are not current requirements.
- Maintain supported legacy saves through explicit migrations.
- Use the existing Python/Pygame stack and existing quality tools before considering new dependencies.
- Rebuild documentation from verified implementation; deleted drafts are not automatically restored.

## Goals / Non-Goals

**Goals:**

- Establish a test-backed baseline before structural refactoring.
- Make run-scoped and map-scoped state explicit.
- Make campaign progression, map activation, and save/load deterministic and recoverable.
- Reduce `Game` to a composition root and thin loop coordinator through staged extraction.
- Support data-driven growth in missions, objectives, maps, enemies, and narrative triggers.
- Make architectural drift, malformed content, and test side effects visible in CI.

**Non-Goals:**

- Replacing the object model with an ECS.
- Implementing quests, dialogue, companions, magic, portals, or Z-level gameplay in this change.
- Supporting multiple simultaneously simulated worlds.
- Rewriting all rendering or optimizing without measured profiling evidence.
- Reintroducing every deleted design draft or release note.
- Changing combat balance, controls, visual identity, or content merely to fit the new boundaries.

## Decisions

### 1. Use characterization-first staged refactoring

Before moving responsibilities, add tests around campaign transitions, save round-trips, boss spawn failure, combat completion order, statistics semantics, and map contracts. Correctness fixes then land before large extraction.

This is preferred over a rewrite because existing local mechanics have broad unit coverage and a rewrite would obscure whether behavior changes are intentional. The alternative of extracting classes first was rejected because the most critical flows currently have no safety net.

### 2. Split state by lifetime

Introduce three explicit lifetimes:

```text
+---------------- Application ----------------+
| GameLoop + SceneRouter + services            |
|                                              |
|  +--------------- RunSession -------------+  |
|  | player + campaign + cumulative stats    |  |
|  |                                        |  |
|  |  +------------ MapSession -----------+ |  |
|  |  | world + enemies + projectiles     | |  |
|  |  | pickups + objective runtime       | |  |
|  |  +-----------------------------------+ |  |
|  +----------------------------------------+  |
+----------------------------------------------+
```

A mission transition replaces `MapSession` and retains `RunSession`. Starting or loading a game replaces the complete `RunSession`. This makes pickup leakage and state-dependent loading structurally harder.

An event bus is not introduced initially. Typed return values and a small set of domain events are sufficient for current scale and easier to trace.

### 3. Keep `Game` as composition root, not application service

Extract responsibilities in this order:

1. A scene/state router owns legal transitions and delegates input/update/render.
2. A campaign service owns mission activation, completion, advancement, and map-session replacement.
3. A combat resolver owns attack effects, damage results, kills, loot, and statistics events.
4. A persistence service serializes and constructs complete sessions.
5. An autosave controller owns timing and policies.

`Game` wires these objects and runs the clock. Scene objects may coordinate presentation but cannot read save files or global configuration directly.

Separate controllers were chosen over a deep inheritance hierarchy because current states share services but differ in behavior. A general command/event bus remains a future option only if typed direct interactions become unmanageable.

### 4. Make campaign definitions data-driven after lifecycle correctness

Represent campaign and mission definitions as immutable typed data loaded from a validated repository-owned format. Definitions include stable IDs, map ID, title, objective definition, and target spawn policy. Runtime objective state remains separate from definitions.

Registries map stable type IDs to objective and enemy constructors. Adding another mission or objective should not require modifying the main loop.

Data-driven definitions are delayed until after the current hard-coded two-mission flow is characterized. Otherwise data migration and behavior correction would be mixed in one step.

### 5. Treat maps as validated content

Separate map definition/loading/validation from runtime world and rendering:

```text
Map files --> parser --> validated MapDefinition --> MapSession
                    |             |
                    +--> errors   +--> collision/render indexes
```

Pixel dimensions derive from validated rows, columns, and tile size. Ground and overlay layers must align. Unknown symbols, missing required spawn points, and missing files are errors. The current fallback to an empty world is removed from production paths; test helpers may construct explicit empty maps.

`World` is decomposed incrementally into runtime model, collision/reachability services, and render/minimap components. Rendering optimization follows profiling, though tile iteration should at minimum be constrained to visible ranges.

### 6. Centralize combat outcome semantics

Weapons produce typed attack commands/effects; the combat resolver applies them and returns typed results such as actual health damage, shield absorption, kill, and generated drops. Projectile and melee paths use the same outcome semantics.

This removes weapon-specific burst/projectile knowledge from the loop and prevents statistics from depending on which attack branch executed. Mission completion is evaluated after combat outcomes and loot are finalized.

### 7. Replace best-effort persistence with transactional session loading

Define typed save DTOs per aggregate and a current schema that includes stable campaign, mission, map, objective, player, statistics, and map-session identifiers/state. Legacy versions pass through explicit sequential migrations.

Load is two-phase:

```text
read -> parse -> migrate -> validate -> construct candidate session
                                      |
                                      +--> failure: active session unchanged

candidate session -> atomic active-session swap
```

Save uses temporary-file write, flush, and atomic replacement. One load/apply path serves quickload and menu load. Display names never serve as persistent IDs.

Schema `1.4` remains readable but is frozen. The exact next version is selected during implementation after the DTO is finalized; compatibility behavior is already fixed by the spec.

### 8. Replace global configuration access incrementally

Parse configuration once into immutable typed settings grouped by domain. Inject only the relevant settings into constructors. During migration, a compatibility adapter can expose existing values, but new application/domain code must not call the global accessor.

Hard-coded values that duplicate configuration are either removed or the misleading configuration option is retired. Paths are resolved from an explicit application root, never the process working directory.

### 9. Rebuild a small authoritative documentation set

The target documentation structure is:

```text
README.md                 player overview, installation, controls
README_RU.md              Russian equivalent
CONTRIBUTING.md           setup, tests, formatting, workflow
docs/architecture.md      current runtime boundaries and diagrams
docs/testing.md           test layers, fixtures, quality gates
docs/decisions/           only durable accepted ADRs when needed
openspec/specs/           normative capability behavior
```

OpenSpec describes required behavior; architecture docs describe current implementation; backlog items live in issues or active OpenSpec changes. Deleted speculative drafts remain absent unless a still-relevant idea is rewritten into the appropriate authority level.

### 10. Establish layered tests and enforceable gates

Tests are organized by purpose:

- Unit: objectives, campaign arithmetic, state transitions, combat results, migrations.
- Integration: complete headless campaign and save/load flows.
- Content contract: every shipped map and campaign definition.
- Architecture: selected dependency and import-side-effect rules.
- Smoke: application startup and one deterministic update/render frame.

Shared fixtures own headless Pygame lifecycle, temp save/log roots, deterministic clocks, and catalog reset. Sleeps, developer-specific absolute paths, repository writes, permissive `assert True`, and exception-swallowing tests are removed.

CI initially records the current branch-coverage baseline, then ratchets it upward. Critical campaign, persistence, transition, and map modules receive explicit higher thresholds. Black check, Flake8, pytest, map validation, worktree cleanliness, and a staged mypy scope run on supported Python versions and both Windows and Ubuntu where path behavior matters.

### 11. Isolate or remove misleading placeholders

Unwired item/NPC classes, unused world helpers, duplicate inventory fields, ineffective menu state, and invalid imports are either:

- integrated behind an accepted capability,
- moved to an explicitly experimental area excluded from runtime, or
- deleted.

No placeholder remains importable as though it were a supported runtime feature.

## Risks / Trade-offs

- [Large cross-cutting scope] -> Deliver in ordered phases with characterization gates and independently reviewable commits.
- [Save migration corrupts player progress] -> Preserve fixture saves for every supported schema and require round-trip plus rollback tests.
- [Refactoring changes game feel] -> Freeze controls, timing, combat values, and rendering order in characterization tests before extraction.
- [Stricter map validation exposes existing content defects] -> Add the validator first, correct all shipped maps in the same phase, and report exact locations.
- [Coverage gate initially blocks all work] -> Record an honest baseline and ratchet thresholds; apply strict per-module gates to newly protected critical flows.
- [Scene extraction creates excessive abstractions] -> Extract only responsibilities with demonstrated independent lifecycle or tests; do not introduce a general framework.
- [Data-driven content reduces debuggability] -> Validate definitions at startup and preserve stable IDs plus source-location diagnostics.
- [Cross-platform CI increases duration] -> Keep fast unit/content jobs broad and reserve full integration smoke tests for the required OS matrix.
- [Documentation drifts again] -> Keep the authoritative set small, link it from the README, and validate commands/links in CI where practical.

## Migration Plan

1. Add characterization tests and fixtures without restructuring; freeze save schema `1.4` behavior.
2. Fix lifecycle defects: required boss spawn failure, completion ordering, map-local reset, statistics semantics, map dimensions, invalid enum aliases, and runtime side effects.
3. Add map/campaign validators and correct shipped data and definitions.
4. Introduce explicit run/map sessions and typed combat results while retaining behavior adapters.
5. Implement the new save DTO, migrations, atomic writes, and single transactional load path.
6. Extract scene routing, campaign service, autosave controller, and render coordination from `Game`.
7. Move campaign definitions to validated data and add extension registries.
8. Rebuild authoritative documentation from the resulting boundaries.
9. Enable quality gates progressively, record their baseline, and remove obsolete or misleading tests/placeholders.

Each phase must leave the game runnable and legacy saves readable. Structural changes are rolled back by reverting the current phase; save migration rollout retains the prior reader and fixture corpus until the new format is proven.

## Open Questions

- The long-term supported Python version range can be finalized when CI runtime and Pygame compatibility are measured.
- The campaign definition serialization format can be selected during the data-driven phase; JSON and TOML both satisfy the design if validation and stable IDs remain unchanged.
- Performance budgets for entity count and frame time should be set after profiling the current 240-enemy map on representative hardware.
