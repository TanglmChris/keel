## Why

Issue #388 (owner, 2026-10-19): CLI shift changes still go wrong. keel-maint's hand-off took 3 m 41 s because only `keel tick`, every 300 s, carries it out; kaiwu-ip's `kaiwu-spec-iecc` hand-off sat `pending` for 13 minutes until a tick was run by hand there, because no tick is installed for that repository. `keel tick` stopped keel-maint's old session while it was blocked on a question to the owner (its job state was `working`, only its `status` was not `busy`), interrupting the conversation. And the old session stays listed under the role's name, next to the new one: the owner renamed both by hand.

## What Changes

- On the CLI, `keel shift ready --wake` leaves a detached hand-over waiter that carries the hand-over out every few seconds; the tick stays as the fallback, and a lock keeps the two from starting two sessions.
- The hand-over waits while the old session is busy or its job state is not `done`/`idle` (a session blocked on a question is not finished).
- The hand-over retires the old session: stop it, rename it `<role> · shifted <date time>` by resuming it with `/rename` (measured to keep the session id), stop it again, then start the new session. A failed rename is recorded and does not block.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: the CLI self-shift hand-over is prompt, waits for a finished session, and retires the old session by name.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/shift-change.md` and their zh-CN twins, one published spec, the changelog.
