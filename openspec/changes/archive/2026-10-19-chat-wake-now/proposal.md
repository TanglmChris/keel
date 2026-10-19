## Why

Issue #348 (rtl_ppa_prj coordinator, 2026-10-18): waking a role whose session had ended was done by hand — the coordinator ran `get_session` → `unarchive_session` → `send_message` six times that day. On 2026-10-19 the team moved to background CLI sessions and the owner chose one model-free CLI waker for #348, #356 and #357. Measured that day (memory: CLI background session wake facts): an idle background session is already woken by the chat FileChanged hook, and an exited one comes back with `claude --bg --resume <id> "<prompt>"`, keeping its id only when no other flag is passed.

## What Changes

- A CLI session's hooks record its session id, Claude process id and worktree in the role's presence.
- `keel chat wake now <role>` resumes that role's recorded CLI session with `claude --bg --resume <id> "<pointer to keel chat unread>"` in its worktree when its process has exited, and says the session is running otherwise.
- `keel tick` does the same, once per new addressed record, for every role that is not parked.
- A post, dm or todo to a role whose CLI process has exited names `keel chat wake now <role>`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: a role's ended CLI session is resumed in one step, and the waker the owner installed resumes it.

## Impact

`src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/tick.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
