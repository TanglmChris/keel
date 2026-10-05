## Why

The owner pointed out on 2026-10-05 that Keel's shift change (5.98.0) should not require a `keel chat` role: Keel is used where no chat is set up. In 5.98.0, `ready` and `resume` refuse in a worktree without a role, and only the chat hook, which speaks for bound roles alone, tells a new session that a note waits.

## What Changes

- `keel shift check`, `ready`, and `resume` work in a worktree with no chat role. The note is then kept per worktree, at `keel-chat/shift/worktree/<name>-<id>.md`, still outside every worktree. With a role, it is kept per role as before.
- `request`, `start`, the reply that closes a request, and the on-shift message stay chat features. They run when roles exist and are optional otherwise: without a role, the coordinator tells the session by any means, and the session runs `keel shift resume`.
- A waiting note is announced through `keel context`, and so through the SessionStart projection on every host, rather than through the chat hook. A new session finds it whether or not a role is bound.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the shift change works without a chat role.

## Impact

`src/core/shift.js`, `src/core/context.js`, `plugins/keel/scripts/session-start.js`, `src/core/chat/notice.js`, `scripts/validate_plugin.py`, both shift guides, the published spec, and the changelog.
