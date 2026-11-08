## Why

Issue #516 (plugin 5.217.0, Keel 5.222.0; kaiwu-ip, role `kaiwu-pm-iecc`, 2026-11-08): every message that wakes a role wakes its Claude session twice, and each wake lists every unread record again. A session parked on a question for 25 minutes with about ten messages arriving saw the host show two identical "Stop hook blocking error from command FileChanged" notices per message, each longer than the last. Taken up at the owner's standing request on 2026-11-08 ("继续，除 175，其它都要解").

Cause, confirmed in the code: `writeRecord` appends to `signal/<role>` and to `signal/worktree/<sha16>` for every worktree bound to the role (chat-wake-late-binding D2), and SessionStart of a bound session asks the host to watch both files, so one record is two `FileChanged` events; `file-changed` exits 2 whenever any waking record is unread and prints the whole unread list each time.

## What Changes

- **A record wakes a session once.** For a session id the hook has seen, a waking record is announced by the first `FileChanged` that reaches it and by no later one, however many signal files changed. The claim is made with an exclusive file creation, so two hooks running at the same moment cannot both announce it.
- **A wake lists what is new.** The `FileChanged` notice names the waking records not yet announced to this session and says how many unread there are in total; it no longer repeats the ones already announced. When nothing waking is new, the hook exits 0.
- **What SessionStart and a user prompt show counts as announced,** so the first `FileChanged` after them does not repeat it. SessionStart starts a session's claims afresh, since a resumed session has been told nothing.
- **A hook payload without a session id behaves as before** (every unread waking record, every time), since there is nothing to remember it against.
- Unchanged: which records wake (mention, todo, direct group); the signal files and what writes them; `keel chat notice` and `check`, which still list everything unread.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

`src/core/chat/notice.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
