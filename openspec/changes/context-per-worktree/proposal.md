## Why

Issues #241 and #246 (rtl_ppa_prj report and review sessions, 2026-10-05). Several worktrees share one repository. When any live change fails to compile, every session's `keel context` and post-compaction note report `blocked` or `ambiguous`, including sessions that will never own that change. A review, verification, or PM session owns no change at all, and is told after every compaction to select an owner. The owner decided on 2026-10-11: scope the verdict by worktree, and let a session declare itself read-only so it reports one quiet `idle` line. Two follow-up choices were answered the same day: read-only is a list of chat roles in `keel/config.yaml`, and ownership is an `owner:` declaration on the change first, then branch history.

## What Changes

- A change may declare `keel: owner: <role>` in its `.openspec.yaml`. Inference counts it only in a worktree bound to that role.
- With no owner declared, a change committed on another worktree's branch beyond the default branch, and not on this worktree's, belongs to that worktree.
- A change that belongs elsewhere is listed as context, with its status and where it lives, and does not make this session `blocked`, `ambiguous`, or `ready`. Explicit selection still reaches it.
- `read_only_roles:` in `keel/config.yaml` lists chat roles whose sessions own no change. In a worktree bound to one, `keel context` reports one `idle` line naming the role, and the SessionStart/compaction note stops asking to select an owner.

## Capabilities

### Modified Capabilities
- `keel-stateless-continuity`: inference is scoped to the changes that belong to this worktree, and a read-only role infers nothing.

## Impact

`src/core/context.js`, `src/core/config.js`, `plugins/keel/scripts/session-start.js`, `keel/config.yaml` (comments), `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog. Item 3 of #241 (listing recently referenced issues when idle) stays open, as the owner left it.
