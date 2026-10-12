## Why

Issue #313 (2026-10-13): `keel patrol --nudge` (5.121.0) tells a role to change shift when the host reports its context at or above `--shift-at`. The owner's policy is different: within a task, let the host compact; change shift when a complete task is finished — with `ready --wake` if the role already holds its next task, plain `ready` otherwise. A context trigger interrupts long tasks and never shifts a run of short ones. Owner decision, 2026-10-13: the trigger is a closed todo, and context no longer triggers a shift.

## What Changes

- `keel patrol --nudge` nudges a role to change shift when a todo assigned to it has been closed since the patrol last looked. The message names `ready --wake` when the role still has an open todo, and plain `ready` otherwise. Each closure nudges once; the first run only records what is already closed.
- `--context` and `--shift-at` are retired. Passing either is refused, with the reason given.
- `docs/shift-change.md` states the policy: change shift at task boundaries, and compact within a task.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: the shift nudge follows a task's close, not context size.

## Impact

`src/core/patrol.js`, `docs/shift-change.md`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
