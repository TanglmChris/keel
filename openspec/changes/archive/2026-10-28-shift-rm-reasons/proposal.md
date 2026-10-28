## Why

Issue #492, approved by the owner on 2026-10-28 as recommended. A shift feature bug fix, within the 2026-10-14 freeze. In ChipSTRIDE two Keel-delivered CLI hand-overs left the old session in `claude agents` (`removed: []`), and `keel shift status` called it "old session kept, reopen it with `claude attach …`", the sentence for a session kept by `shift: keep_old_sessions:`, which ChipSTRIDE does not declare. The old session was later opened and came back beside the new shift.

Both old sessions had moved into a worktree they created with `EnterWorktree`, and the new shift was started in that same worktree. `claude rm` deletes "a background session and its worktree" (`claude rm --help`, Claude Code 2.1.311), so a removal that had worked would have deleted the new shift's worktree; the first hand-over's old session, removed later, took its worktree and branch with it.

## What Changes

- **The session a hand-off names is always a candidate for removal,** wherever its row's working directory is. Its transcript is also looked for in the project directory of the worktree the host records for it.
- **A session whose own worktree is in use is not removed.** Before `claude rm`, Keel reads the worktree the host records for the session (`<config>/jobs/<id>/state.json` `worktreePath`). When it is the hand-off's worktree, a worktree bound to a role, or another listed session's working directory, the session stays, with that reason.
- **Every old session left in place records why** on the hand-off: kept by `keep_old_sessions`, still running, its transcript could not be copied, its worktree is in use, or `claude rm` failed with its exit status and message.
- **`keel shift status` says so** instead of borrowing the keep sentence: an old session not removed is named with its reason, and with the warning that opening it brings it back beside the new shift.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `docs/host-contract.md`, the published spec, and the changelog.
