## Why

Issue #293 (2026-10-12): a role with no coordinator above it — the PM going last after #289, or any session changing its own shift — has nobody to start its next session once it clears, so it stays dark until a person types. Walking the PM's own shift also found that `ready` tells such a role a coordinator will wake it, that `keel shift start` accepts a role starting itself and wakes nothing, and that a new shift opened in another worktree cannot find the role's note. The owner decided on 2026-10-12: a one-shot delayed self-wake, stated as an exception to "Keel schedules nothing".

## What Changes

- `keel shift ready --wake` leaves a detached one-shot waiter. Once the role's next session has started — a SessionStart with source `clear` or `startup` later than the `ready` — it writes one wake record addressed to the role and exits. It writes nothing if the note was already resumed, and gives up after two hours. The chat SessionStart hook records when and how a session started, for the waiter to read.
- `ready` without `--wake`, for a role no request named, says that nobody will start the new session and names `--wake`.
- `keel shift start` refuses a role starting itself, naming `ready --wake`.
- `keel shift resume --role <role>` reads a role's note from a worktree bound to no other role.
- `status` says a self-filed note is resumed by the role's own next session.
- `AGENTS.md` and the README state the one exception to "Keel schedules nothing".

## Capabilities

### Modified Capabilities
- `keel-shift-change`: a session changes its own shift, woken by a one-shot waiter.
- `keel-unattended-triage`: "Keel ships no scheduler" names the shift wake as its one exception.

## Impact

`src/core/shift.js`, `src/core/chat/notice.js`, `AGENTS.md`, `README.md`, `docs/shift-change.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
