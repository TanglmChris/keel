## Why

Issue #434, approved by the owner on 2026-10-21. `patrol:` declares one role (`readPatrolDeclaration` in `src/core/config.js`). kaiwu-ip runs one coordinator per IP team: `kaiwu-pm-iecc`, and now `kaiwu-pm-rmw`, each with its own chat group. With `patrol: role: kaiwu-pm-iecc`:

- the second coordinator gets no re-arm reminder and no host task of its own;
- the IECC coordinator's `--nudge` covers every bound role, so it nudges the RMW team's roles;
- the risks those nudges raise are reported to a coordinator who does not manage that team;
- `keel tick` runs one patrol only.

## What Changes

- **`patrol:` may be a list.** Each item is opened by `- role:` and carries the keys a single mapping carries today, plus `scope: group:<name>`. The single mapping keeps its meaning: one patrolling role over the whole repository.
- **A declaration covers the roles it coordinates.** A scoped one covers the members of its chat group. The unscoped one covers the roles in no scope. A role in two scopes is covered by both, and nudged at most once per window (owner, 2026-10-21). Nudges, their escalations, presence rows, snapshot entries, hand-off risks, and issue routing follow that coverage.
- **Repository-wide risks reach one coordinator.** The remote tip, the shared checkout, binding drift, disk, and quota go to the unscoped declaration, or to the first declared when every declaration is scoped (owner, 2026-10-21).
- **Each coordinator gets its own reminder, host task, and cadence.** `keel patrol task` renders the declaration of the role bound to the calling worktree, or of `--role <role>`.
- **`keel tick` runs each declared patrol when it is due.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/config.js`, `src/core/context.js`, `src/core/shift.js`, `src/core/patrol.js`, `src/core/tick.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the README in both languages, the `keel/config.yaml` comment, the published spec, and the changelog.
