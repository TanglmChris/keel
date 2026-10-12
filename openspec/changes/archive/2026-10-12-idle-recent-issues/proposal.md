## Why

Issue #278, split from #241 item 3 (rtl_ppa_prj report and review sessions, 2026-10-05): after compaction, an idle session has nothing pointing at what it was last doing except its own memory. The branch's own commits already say which issues it was working on.

## What Changes

- When `keel context` reports `idle`, it carries `recent`: up to five issue numbers referenced (`#<n>`) by this branch's commits beyond the default branch, newest first, with the range they came from. It is a pointer and selects nothing; it is absent on the default branch, with no default branch, or when no commit references an issue.
- The SessionStart and compaction projection prints it on one line.
- The reader is shared with `keel worktrees`, which already lists a branch's referenced issues.

## Capabilities

### Modified Capabilities
- `keel-stateless-continuity`: an idle result points at the issues the branch's recent commits reference.

## Impact

`src/core/worktrees.js`, `src/core/context.js`, `plugins/keel/scripts/session-start.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
