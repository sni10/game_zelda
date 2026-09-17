## 1. Establish the Characterization Baseline

- [x] 1.1 Add shared headless Pygame fixtures, deterministic clocks, and temporary save/log roots; verify the full test suite leaves the repository worktree unchanged.
- [x] 1.2 Replace developer-specific absolute map paths and working-directory mutation in tests with repository fixtures; verify the affected tests pass on Windows and a path-independent temporary directory.
- [x] 1.3 Remove or rewrite permissive tests that pass after caught exceptions or `assert True`; verify each replacement fails when its target behavior is deliberately broken.
- [x] 1.4 Consolidate duplicate save-system tests and stop writes to `saves/quicksave.json`; verify all save tests use `tmp_path` and preserve existing supported-version coverage.
- [x] 1.5 Add unit tests for mission objectives, campaign baselines/deltas/totals, advancement, and final completion; verify all campaign lifecycle branches are asserted.
- [x] 1.6 Add tests for mission-complete screens and map transition input, fade phases, large `dt`, and callback exactly-once behavior; verify deterministic completion without sleeps.
- [ ] 1.7 Add a headless integration test for new game through boss defeat, mission completion, map transition, second mission, and campaign completion; verify run-scoped state persists and map-scoped state resets.
- [ ] 1.8 Add characterization tests for current save schemas `1.0` through `1.4`, actual map restoration, failed-load rollback, and quickload/menu-load equivalence; verify fixtures remain readable before changing persistence.

## 2. Correct Campaign and Runtime Defects

- [ ] 2.1 Make required objective-target spawn failure abort mission activation with a visible error; verify a failed boss spawn cannot auto-complete a mission.
- [ ] 2.2 Reorder combat, defeat, loot, statistics, and objective processing so a completing kill resolves once and completely; verify boss loot and defeat statistics exist before the completion screen.
- [ ] 2.3 Reset enemies, projectiles, pickups, objective runtime, and other map-local state during transition while preserving player/run state; verify no prior-map entity survives.
- [ ] 2.4 Define and implement stable statistics semantics for attack attempts, actual health damage, shield absorption, healing, items, active play time, and movement; verify focused tests exclude teleports and paused time.
- [ ] 2.5 Give burrow entrance and exit distinct terrain identifiers and migrate map parsing accordingly; verify both markers can be loaded and distinguished.
- [ ] 2.6 Remove import-time Pygame initialization and broken runtime imports from utility/placeholder modules; verify importing every production module has no display initialization or missing-module failure.
- [ ] 2.7 Resolve application data, save, and log paths from an explicit application root; verify game startup and persistence work when launched outside the repository directory.

## 3. Enforce Map and Mission Content Contracts

- [ ] 3.1 Introduce a typed map definition and parser result that records dimensions, layers, symbols, and spawn metadata; verify parser unit tests cover valid and malformed input.
- [ ] 3.2 Implement fail-fast validation for missing files, empty/non-rectangular maps, unknown symbols, mismatched overlays, and invalid spawn counts; verify diagnostics include file and location.
- [ ] 3.3 Derive runtime dimensions from map rows, columns, and tile size and remove contradictory mission/config duplication; verify `main_world` and `big_world` dimensions match their loaded definitions.
- [ ] 3.4 Validate mission map references, required objective-target placement, and reachability before starting play; verify invalid shipped-style fixtures are rejected.
- [ ] 3.5 Add a non-interactive all-content validation command; verify it accepts every corrected file under `data/` and exits nonzero for a malformed fixture.
- [ ] 3.6 Correct existing map, overlay, mission, and configuration inconsistencies exposed by validation; verify the content command and map tests pass with no silent fallback.

## 4. Introduce Explicit Runtime Lifetimes

- [ ] 4.1 Add a run-session model for player, campaign, and cumulative statistics with compatibility accessors for the current coordinator; verify new-game construction preserves current defaults.
- [ ] 4.2 Add a map-session model for world, enemies, projectiles, pickups, and objective runtime; verify replacing it cannot retain prior-map entities.
- [ ] 4.3 Move mission activation and advancement into a campaign service that constructs complete candidate map sessions; verify activation failure leaves the active session unchanged.
- [ ] 4.4 Route new game, mission transition, restart, and load through the same session replacement boundary; verify state-transition integration tests cover every entry path.

## 5. Unify Combat Outcomes

- [ ] 5.1 Define typed attack, damage, kill, and drop results with stable damage/shield semantics; verify unit tests cover melee, ranged, burst, shotgun, AoE, and contact damage.
- [ ] 5.2 Introduce a combat resolver used by melee and projectile paths; verify identical outcomes produce identical statistics and loot regardless of weapon transport.
- [ ] 5.3 Move projectile/burst/pellet orchestration out of the main loop behind weapon attack results; verify adding a test weapon does not require changing the loop coordinator.
- [ ] 5.4 Ensure enemy separation and knockback respect world collision and bounds; verify enemies cannot be displaced into blocked terrain.

## 6. Make Persistence Transactional

- [ ] 6.1 Define typed current-schema DTOs with stable IDs for campaign, mission, map, objectives, player, catalogs, statistics, enemies, projectiles, and pickups; verify validation rejects unknown IDs and invalid ranges.
- [ ] 6.2 Implement explicit sequential migrations for every supported schema through `1.4`; verify golden fixtures migrate to the same current DTO.
- [ ] 6.3 Serialize the actual active run/map/campaign state instead of global defaults or display names; verify a save from each mission restores the same mission and objective state.
- [ ] 6.4 Build and validate a complete candidate run before swapping active state; verify malformed saves leave the current game byte-for-byte behaviorally unchanged.
- [ ] 6.5 Replace duplicate quickload and menu-load application paths with one transactional loader; verify both entry points produce equivalent sessions and errors.
- [ ] 6.6 Write saves through a temporary file and atomic replace; verify an injected write failure preserves the prior valid save.
- [ ] 6.7 Remove obsolete empty/duplicated persistence fields or migrate them explicitly; verify legacy fixtures retain intended coins, equipment, and inventory meaning.

## 7. Decompose Application Orchestration

- [ ] 7.1 Introduce an explicit scene/state router with a tested legal transition table; verify menu, play, inventory, save/load, game-over, mission-complete, transition, and campaign-complete routes.
- [ ] 7.2 Move autosave timing and policy into an injected controller; verify deterministic clock tests cover interval, rotation, pause behavior, and disabled autosave.
- [ ] 7.3 Separate world runtime/collision concerns from world and minimap rendering without changing draw order; verify render characterization and collision tests remain unchanged.
- [ ] 7.4 Remove direct persistence access from presentation components by passing view models and actions; verify an architecture test rejects presentation-to-persistence imports.
- [ ] 7.5 Replace new global configuration reads with immutable typed settings injected by domain; verify configuration validation covers every consumed key and no new application/domain module imports the global accessor.
- [ ] 7.6 Reduce the main game class to composition, loop timing, and top-level delegation; verify campaign, combat, persistence, and scene tests run without constructing the full application.

## 8. Prepare Content-Driven Scaling

- [ ] 8.1 Select a repository-owned campaign definition format and define its schema with stable IDs and source-location diagnostics; verify the current two missions parse to equivalent definitions.
- [ ] 8.2 Add objective and enemy registries that construct runtime behavior from validated type IDs; verify a test objective and enemy can be registered without modifying campaign orchestration.
- [ ] 8.3 Move the current hard-coded campaign into validated data while keeping objective runtime state separate; verify the end-to-end campaign test remains unchanged.
- [ ] 8.4 Profile the 240-enemy large map and record frame-time, render iteration, collision, minimap, and separation baselines; verify results are reproducible with a deterministic seed.
- [ ] 8.5 Apply only profiling-supported spatial/render optimizations such as visible tile ranges or spatial hashing; verify benchmark improvement and unchanged gameplay tests.
- [ ] 8.6 Classify each unwired item/NPC/helper/menu placeholder as integrate, experimental, or remove and apply the decision; verify all remaining production modules are reachable or intentionally documented.

## 9. Restore Documentation and Quality Governance

- [ ] 9.1 Create concise English and Russian READMEs from verified behavior with install, launch, controls, campaign, save, and troubleshooting information; verify commands and internal links.
- [ ] 9.2 Create a contributor guide with supported environments, dependency setup, formatting, lint, typing, test, OpenSpec, and branch workflow commands; verify every documented command runs.
- [ ] 9.3 Create the current architecture document with runtime flow, dependency direction, run/map lifetimes, extension points, persistence, and scaling constraints; verify module references match the implemented tree.
- [ ] 9.4 Create the testing guide with test layers, shared fixtures, data contracts, coverage policy, and regression expectations; verify it matches test configuration and CI.
- [ ] 9.5 Keep deleted speculative documents absent or recover only still-relevant material as explicitly historical/decision content; verify no current documentation links to obsolete drafts.
- [ ] 9.6 Configure Black, Flake8, pytest/coverage, and an incremental mypy scope in repository configuration; verify local check commands return successfully.
- [ ] 9.7 Add CI jobs for formatting, linting, branch coverage, content validation, architecture checks, and worktree cleanliness; verify intentional violations fail their corresponding jobs.
- [ ] 9.8 Measure supported Python/Pygame combinations and add the justified Windows/Ubuntu matrix; verify all required jobs pass on the selected versions.
- [ ] 9.9 Record an honest coverage baseline and stricter thresholds for campaign, persistence, transitions, and map validation, then document a ratcheting policy; verify the configured gates reject regressions.
- [ ] 9.10 Run the full quality suite and a manual campaign/save smoke test, reconcile all capability scenarios with evidence, and verify the repository is ready to archive this OpenSpec change.
