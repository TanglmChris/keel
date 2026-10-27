## Why

Issue #483, approved by the owner on 2026-10-27, who chose the first option there and its refusing form. `keel branches` finds a role's task branches only through the HEAD reflog of a worktree bound to the role, so a binding's removal makes the branches only that worktree checked out unreachable: no listing names them and `keel branches prune` can never delete them. On 2026-10-26 the role `keel-maint-2` was unbound that way and left five local and four remote merged branches that had to be deleted by hand.

## What Changes

- **`keel chat role --unset` refuses to strand merged branches.** When unbinding the worktree would leave merged task branches of its role that no other bound worktree reaches, it exits 2, changes nothing, names each such branch, and points at `keel branches prune` and at `--leave-branches`.
- **`--leave-branches` unbinds anyway** and names the branches `keel branches` will no longer list.
- An unset that strands nothing behaves as before.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

`src/core/chat/cli.js`, `src/core/branches.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, the README in both languages, the published spec, and the changelog.
