## Why

On 2026-10-19 the agent team moved to background CLI sessions, where a session cannot clear itself: `/clear` needs a person attached to it. The owner chose that a CLI self-shift stops the old session and starts a new one — a clean context, as the clear gave — and that the old session is kept and findable, and that the one CLI waker (`keel tick`) carries it (#357, merged with #348 and #356). Issue #357 also asked for one runner with a queue instead of a host task per role, and for the queue to be visible. #346 (a wake queued during the desktop shift turn refused the clear) belongs to the desktop clear path this team no longer runs.

## What Changes

- `keel shift ready --wake` in a Claude Code CLI session records `CLI session:` and `CLI process:` in the note and queues the hand-off in the chat store instead of arming the desktop waiter; it tells the session to end its turn and that `keel tick` hands over.
- `keel tick` takes each queued hand-off once the old session is idle or gone: it stops it with `claude stop` (kept: `claude attach` reopens it), starts a new session with `claude --bg -n <role> --permission-mode <mode> "<run keel context, then keel shift resume>"` in the role's worktree, and records `delivered` with the new session id, or `failed` with the reason.
- `keel shift status` lists the queue; the patrol reports a failed hand-off, or one pending over 15 minutes, as a risk.
- `shift: permission_mode:` in `keel/config.yaml` sets the new session's mode (default `auto`).

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: a CLI session changes its own shift through the waker's queue.

## Impact

`src/core/shift.js`, `src/core/tick.js`, `src/core/patrol.js`, `src/core/config.js`, `scripts/validate_plugin.py`, one published spec, the changelog. Closes #357 for the CLI and #346 as desktop-only.
