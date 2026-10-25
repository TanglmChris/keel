## Why

Issue #465. After the workspace was renamed from `~/my_github` to `~/my-github` on 2026-10-25, no role's ended CLI session could be woken. `keel chat wake now <role>` resumes in the worktree that presence recorded, which is still the old path, and Claude Code resumes a session only in the directory it registered. Run from the new path, the resume printed `Workspace not trusted. /Users/…/my_github/… could not be resolved on disk`, and nothing started. All 16 kaiwu-ip roles with a recorded session hit it, and each was recovered by hand with `claude --bg --fork-session --resume <id>` in its new worktree.

The owner decided (2026-10-25) that Keel names the cause and prints the fork command, and lists the affected roles, without forking by itself: `wake now` stays a plain resume.

## What Changes

- **`keel chat wake now` explains a session whose directory is gone.** When the directory a recorded CLI session ran in no longer exists, it resumes nothing and exits nonzero. It says why, and prints a fork command to copy: `cd <role's worktree> && claude --bg --fork-session --resume <id> -n "<role> · <time>" --permission-mode <mode> "<prompt>"`. The fork starts a new session with the whole conversation, and its first hook records it, after which waking works again.
- **`keel tick` does not retry it.** A tick that meets such a session marks that record handled, as it does for a removed session, and asks the host nothing.
- **`keel patrol` and `keel shift status` list such roles.** Each one named reads as a role whose recorded CLI session ran in a directory that no longer exists, pointing at `keel chat wake now <role>`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

The change touches:
- `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/tick.js`, `src/core/patrol.js`, `src/core/shift.js`;
- `scripts/validation/chat.py`, `scripts/validation/registry.py`;
- the published spec and the changelog.

Nothing forks a session by itself. A renamed or moved worktree now reads as one named cause with one command to run, instead of a host error to decode.
