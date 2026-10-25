## Why

Issue #462. On 2026-10-25 the owner asked that a shift change leave no old session in `claude agents` (or make that optional, with none kept by default). The default has been none since 5.178.0 (#418), so the gap is not the default. On 2026-10-25, `claude agents --json --all` still listed old shifts that bypass the removal, in three ways:

- A takeover that does not go through Keel's hand-over. After the workspace rename, the owner opened a new session, which ran `keel shift resume`. `resume` removes nothing, so `keel-maint · 10-21 22:06` (`6fffda34`) stayed listed.
- Sessions left by hand-overs before 5.178.0. kaiwu-ip's roles from 10-20 (`kaiwu-flow`, `kaiwu-lead`, and others) are still listed in pairs, because removal waits for each role's next hand-over.
- Sessions whose working directory no longer exists. The removal matches a row by its `cwd` against `roles.json`, which the rename rewrote to `my-github`. Every pre-rename row still reads `/Users/my_home_mac/my_github/...`, so no later hand-over would ever match it.

The owner chose one fix: `resume` removes old sessions too. The shift feature is frozen, and this is a bug fix within it: no new command, no new declaration, no new default.

## What Changes

- **`keel shift resume` removes the role's old sessions.** Run in a Claude Code session, after it prints a note that a CLI session wrote, `resume` runs the hand-over's removal for the role under `shift: keep_old_sessions:`. The protections are the same: only stopped background sessions, only once Keel's store holds the transcript, never one whose process still runs, and never the current session. It prints the removed ids and how to read them. When Keel's own hand-over already removed them for this session, it does not ask the host again.
- **An old session is the role's by Keel's record too.** A stopped row counts as the role's when its working directory is a bound worktree, as before, or when Keel's store keeps its transcript under the role, whatever its working directory. A renamed or moved worktree no longer strands its old sessions.
- **`docs/cli-team.md` and its Chinese page** say so.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

The change touches:
- `src/core/shift.js`;
- `docs/cli-team.md`, `docs/cli-team.zh-CN.md`;
- `scripts/validation/shift.py`, `scripts/validation/registry.py`, the published spec, and the changelog.

At a role's next `resume` in a Claude Code session, its old listed sessions are removed, each only after Keel holds its transcript, the pre-5.178.0 and pre-rename ones included.
