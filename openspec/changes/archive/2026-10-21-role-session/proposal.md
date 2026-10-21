## Why

Issue #415, approved by the owner on 2026-10-21. A role's recorded CLI session — the one `keel chat dm` names and `keel chat wake now` resumes — can end up on the wrong session. On 2026-10-20 in kaiwu-ip:
- `kaiwu-lead` was recorded with a visiting `kaiwu-chief` session as its previous session, and a removed session as its current one.
- `keel chat role --set kaiwu-lead` in the live session changed nothing.

On 2026-10-21 the same family of failures was reproduced in this repository. keel-maint-2 was started with `claude --bg -w keel-maint-2` from the main checkout. When it was later resumed, its SessionStart hook reported the main checkout as `cwd`. So:
- the session was recorded as `codex-issues`' CLI session, with the main checkout as its worktree;
- it watched codex-issues' signal instead of its own;
- a direct message to keel-maint-2 did not wake it.

Earlier, `keel chat wake now keel-maint-2` found no session at all, because the role was bound after the session started.

## What Changes

- **A chat hook resolves the session's real worktree.** When the transcript's project directory names another worktree of this repository than the hook's `cwd`, the hook uses that worktree.
- **A `keel chat` command no longer records a visiting session.** It records the calling session as the role's session only if that session started as the role. Otherwise it leaves the role's recorded session, worktree, and session list as they were. A caller that is not a Claude session leaves them as they were too, instead of clearing them.
- **`keel chat role --set <role>` records the session that binds the role.** Run inside a Claude Code session, it records that session, its process, and its worktree as the role's. It also writes the session's own record, and starts the role's current transcript segment with this session's transcript.
- **`keel chat wake now` and the tick do not resume a removed session.** If the recorded session has exited and `claude agents --json --all` no longer lists it, they resume nothing and say so.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

`src/core/chat/notice.js`, `src/core/chat/cli.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
