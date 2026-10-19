## Why

Issue #369 point 4 (rtl_ppa_prj, 2026-10-18 21:37–22:20): the owner ran `claude --resume <desktop PM session id>` in a terminal, leaving the desktop original and the CLI copy both live in one worktree, both bound to `iecc-pm`. Both posted as `iecc-pm`, so other roles could not tell which spoke; the one read cursor let whichever read first hide records from the other; each held owner decisions the other lacked. Keel did not notice: presence is one file per role, and the last writer wins. The owner chose on 2026-10-19 to do #369's remaining points.

## What Changes

- Each session that writes a role's presence also records itself — session id, Claude process, worktree, last activity — under the role, and drops entries whose process has ended.
- With two or more live sessions on one role, `keel context` warns, and `keel chat post`, `keel chat unread` and `keel chat read` warn on stderr, naming the role, the sessions and that they share one name and one read cursor.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: two live sessions on one role are reported.

## Impact

`src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/context.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
