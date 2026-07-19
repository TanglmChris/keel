## Why

Deferred work needs a durable owner that is not chat history and not `keel/HANDOFF.md`.

Keel requires unresolved follow-ups to live in a current OpenSpec task, a new OpenSpec change, archive evidence, or an explicit discard reason. This change is the dedicated owner for project follow-ups that are worth tracking but intentionally out of scope for the current task.

## What Changes

Create `openspec/changes/follow-up-backlog/` as the standing follow-up project.

Future deferred items should be added to `tasks.md` only when they are actionable enough to own. Each item should include evidence/rationale and, when it becomes executable, the normal Keel task contract: Owner, Mode, Read, Touch, Commands, Acceptance, Autonomy boundary, Stop Rules, Evidence, Stop if, and Report.

## Capabilities

### New Capabilities

- None. This is a process/ownership change, not a product capability.

### Modified Capabilities

- None.

## Impact

- Establishes `openspec/changes/follow-up-backlog/tasks.md` as the durable owner for deferred project work.
- Keeps `keel/HANDOFF.md` pointer-only.
- Keeps `keel/archive/` for historical evidence and snapshots, not active follow-up ownership.
