## Why

Issue #260, the step the owner deferred on 2026-10-11: the coordinator runs `keel patrol` from a host schedule (Claude Code's session-scoped cron), which ends with the session — a shift change's `/clear` or a restart loses it, and nothing tells the new shift to re-create it. The owner decided on 2026-10-12: remind the new shift; Keel still schedules nothing.

## What Changes

- `keel/config.yaml` may declare `patrol:` with `role: <role>` and `every: <duration>`.
- In a worktree bound to that role, `keel context` carries `patrol`, the SessionStart and compaction projection says this role runs `keel patrol` every `<every>` and that a session's schedule ends with the session, and `keel shift resume` ends with the same reminder.
- An unreadable declaration is reported and reminds nobody.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: the patrolling role is reminded to re-arm its schedule.

## Impact

`src/core/config.js`, `src/core/context.js`, `src/core/shift.js`, `plugins/keel/scripts/session-start.js`, `keel/config.yaml` (comments), `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
