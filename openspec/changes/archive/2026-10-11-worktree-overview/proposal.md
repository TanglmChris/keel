## Why

Issue #243 (PM of rtl_ppa_prj, via rtl_ppa_flow, 2026-10-05): the coordinator builds a status summary of every session by hand. That covers each worktree's branch and head, ahead/behind against its upstream, the last commit, the bound chat role and presence, and the issues the branch references. On 2026-10-05 it misread one remote state, and a zsh `for` loop pitfall cost another attempt.

## What Changes

- New read-only `keel worktrees [--repo <path>] [--issues <file>] [--json]`. For each worktree of the repository it lists the path, the branch or detached head, the short head, ahead/behind against the upstream as of the last fetch, the last commit's subject and time, the number of uncommitted paths, the bound chat role with its presence, and the issue numbers referenced by commits on the branch that the default branch does not contain.
- With `--issues <file>` holding what `gh issue list --json number,updatedAt` returned, each referenced issue is shown with its last update. Keel never fetches.

## Capabilities

### New Capabilities
- `keel-worktree-overview`: a read-only overview of every worktree of a repository.

## Impact

New `src/core/worktrees.js`, `bin/keel.js`, `scripts/validate_plugin.py`, `README.md`, the published spec, and the changelog.
