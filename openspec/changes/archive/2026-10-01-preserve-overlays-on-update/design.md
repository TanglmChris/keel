## Context

F1 — On 5.85.0, runAction forwards OpenSpec arguments without overlay recovery. Basis: bin/keel.js, inspected 2026-10-01.
F2 — Doctor counts overlays only for options.target. Basis: printTargetSurface and runDoctor in bin/keel.js.
F3 — The shared surface list handles Claude, legacy Codex, .agents Codex, and OpenCode. Basis: openspecOverlaySurfacesForTarget.

## Goals / Non-Goals

Goals: resolve #186 without requiring repeated target installs; expose missing overlays across targets.
Non-goals: new install commands, dependencies, host hook reload, #190 policy changes.

## Decisions

D1 — After a successful `keel openspec update`, discover installed targets from repository OpenSpec surfaces and replay existing overlays using the shared list. Basis: #186 option 1, accepted user instruction to implement. Discover again after update because upstream may change layout. Do not create missing files.
D2 — Doctor keeps its selected target report and adds separately named overlay health lines for other installed targets. Basis: #186 option 2. Discovery considers skills and repository command files; global prompts alone must not enroll an unrelated repository.
D3 — Failed upstream commands return their exact nonzero status with no replay; other OpenSpec commands remain passthrough. Basis: preserving CLI compatibility and honest error reporting. Replay errors fail the command rather than claiming success.
D4 — Tests exercise public CLI with real OpenSpec updates in temporary repositories, including repeat updates, stripped foreign-target overlays, and failure without mutations. Basis: regression-first discipline.

## Hidden Knowledge / Assumptions

None. No matching domain lens or available precedent is required for this CLI defect.

## Risks / Trade-offs

An upstream update may change Codex layout; post-update discovery and both-layout checks prevent stale target enumeration. Doctor's additional lines are informational and do not imply hooks ran.

## Open Questions

None.
