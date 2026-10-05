## Why

rtl_ppa_flow tried `keel shift check` 5.99.0 on 2026-10-06 in its worktree. The check reported three temporary worktrees created by other sessions in their Claude scratchpads, and so said not ready. As written, one session's leftover temporary worktree blocks every session of the repository from changing shift.

## What Changes

- A temporary linked worktree counts as this worktree's loose end only when it lies in a Claude scratchpad of a session started in this worktree. Claude keeps scratchpads under `claude-<uid>/<slug>/<session>/scratchpad/`, where the slug is the session's directory with every non-alphanumeric character turned into `-`.
- Every other temporary linked worktree is listed as a note with its path, which does not affect readiness. That covers another session's scratchpad and a temporary directory whose owner cannot be told.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the readiness check counts only temporary worktrees attributable to this worktree.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, the shift guides, the published spec, and the changelog.
