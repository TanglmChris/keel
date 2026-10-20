## Why

Issue #403 (kaiwu-ip, 2026-10-20 09:38–09:40): `kaiwu-design-iecc` held the `cpu-heavy` lease with `kaiwu-pm-iecc` waiting. Its release failed with `Group "dm-kaiwu-design-iecc--kaiwu-pm-iecc" is not a valid name: use ^[a-z0-9][a-z0-9-]{0,31}$.`, and so did the expiry sweep and `keel lock list`. The lease blocked everyone until a role with a short enough name happened to run a lock command. Since the 2026-10-19 rename, most pairs of kaiwu role names join into a direct group name longer than 32 characters, so the same failure blocks `keel chat dm` between them as well.

## What Changes

- A direct group's name is valid when it is `dm-<a>--<b>` with two different valid role names in sorted order, whatever its total length. Every command that takes, lists, or authorizes a group name accepts it.
- `keel lock release` and the expiry sweep free the lease first and then tell the waiters. A notice that cannot be posted is printed as a warning and does not fail the command.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: direct groups between long role names.
- `keel-resource-lock`: freeing a lease does not depend on its notice.

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/config.js`, `src/core/lock.js`, `scripts/validate_plugin.py`, the published specs, the changelog.
