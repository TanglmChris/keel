## Why

Issue #254, part of #250 (rtl_ppa_prj, 2026-10-05): three sessions contended for the main checkout, for integration, a rerun after the toolchain upgrade, and a formal sweep record, with no way to claim it. Shared branches and other single-holder resources are the same kind of thing. Each session found out by colliding.

## What Changes

- New `keel lock acquire <resource> --for <duration> --note <why>`, `keel lock release <resource>`, and `keel lock list`. A lease records the holder, its worktree, the expiry, and the note, in the repository's chat store, so every worktree sees it.
- A lease is exclusive. Acquiring one another holder has is refused, naming the holder, expiry, and note, and records the requester as a waiter. The holder may acquire again to renew.
- A lease ends at release or at expiry. Keel schedules nothing, so expiry is noticed by the next `keel lock` command in any worktree, which frees the lease. Release and noticed expiry each post a direct chat message to the holder and every waiter that has a chat role.
- A lock is a coordination signal. It enforces nothing on Git or the filesystem, and `acquire` says so.
- `keel shift check` lists leases the worktree still holds as loose ends.
- Allowing codex in `keel/config.yaml` (`external_agents:`), so this change's implementation can be delegated to it as the owner decided on 2026-10-11.

## Capabilities

### New Capabilities
- `keel-resource-lock`: leases on shared resources between sessions.

### Modified Capabilities
- `keel-shift-change`: the readiness check lists held leases.

## Impact

`keel/config.yaml`, new `src/core/lock.js`, `bin/keel.js`, `src/core/shift.js`, `scripts/validate_plugin.py`, a new guide `docs/resource-lock.md`, `README.md`, the published specs, and the changelog.
