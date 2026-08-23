## Why

The protocol's "one task, then stop" boundary folds two different stops into one. Stops at real decisions — a blocker, fingerprint drift, an out-of-scope need, a material choice `keel-align-expectations` escalates, an unresolved `Q<n>` — each have their own independent trigger and must stay. The stop at a task boundary inside a change whose `tasks.md` the owner already reviewed and approved is different: it re-asks for an approval already given, and Keel has no durable place to record that answer. Reproduced against the current tree (2026-08-17, 5.40.0): `STANDING_AUTHORIZATION_ACTIONS` (`src/core/config.js:10`) has no name for it, and `keel-run-single-task-goal`'s stop rule requires "a new explicit user instruction" — which can only be given in conversation, exactly the channel issue #34 identified as not surviving a context reset. The owner decided on issue #94 (2026-08-17): adopt candidate ② — add `continuation` to the `authorize:` vocabulary, removing only the between-task confirmation, never a gate, evidence, or Review.

## What Changes

- `STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js` gains `continuation`. The doctor's per-action rows, the unrecognized-entry message's accepted-names list, `keel context`'s broken-declaration warning, and capsule inheritance all read the constant and follow without further code change.
- Semantics, stated in spec and docs: a standing `continuation` authorization covers exactly the boundary between a durably complete task and the next unchecked task of the same change, inside a change whose `tasks.md` the owner approved. Each next task still starts through `keel gate task-start` with its own fingerprint; every gate, evidence requirement, semantic Review, and the write guard run unchanged; nothing schedules, and nothing selects work outside the change — task order still comes from the approved `tasks.md`, never from a backlog scan.
- `keel-run-single-task-goal`'s stop rule (both the `src/skills/` and `plugins/keel/skills/` copies) names a standing `continuation` authorization as the durable form of the user instruction it requires before another task starts.
- The `## Execution boundary` section of `AGENTS.md` states the same semantics so the agent enforcing the boundary reads them from the resident protocol.
- `README.md`'s standing-authorization section and `keel/config.yaml`'s comment update their accepted-names enumeration and state what `continuation` covers.
- This repository's own declared `authorize:` list is unchanged: declaring `continuation` here is a separate repository-policy decision the owner has not made.

## Capabilities

### Modified Capabilities
- `keel-standing-authorization`: the closed vocabulary gains `continuation`, and a new requirement states what a `continuation` authorization covers and what it never covers.
- `keel-single-task-goal-execution`: the "Goal execution stops at the selected task boundary" requirement recognizes a standing `continuation` authorization as the durable, repository-declared form of the new user authorization it requires before the next task of the same change starts.

## Impact

- Affected code: `src/core/config.js` (one constant).
- Affected skills: `src/skills/keel-run-single-task-goal/SKILL.md` and its byte-identical `plugins/keel/skills/` copy.
- Affected docs/protocol: `README.md`, `keel/config.yaml` (comment only), `AGENTS.md`.
- Affected tests: `scripts/validate_plugin.py` — its `STANDING_AUTHORIZATION_ACTIONS` tuple, the `standing-authorization` scenario's undeclared-action needles, the `standing-authorization-inert` all-declared fixture, and a new scenario for the `continuation` semantics.
- Owner-decided vocabulary widening (issue #94, 2026-08-17). No new dependency, no schema change, no change to any gate verdict: the word authorizes a decision the workflow already reached, exactly as the existing four do.
