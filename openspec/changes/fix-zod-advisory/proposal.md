## Why

The released lockfile installs Zod 4.4.3, affected by GHSA-mrhx-c7xc-m3w5 (#528). The owner requested this repair and tracker closure for already delivered #526.

## What Changes

- Update only the compatible transitive Zod lock entry to patched 4.6.7; preserve OpenSpec 1.14.0 and its dependency range.
- Verify audit removal, actual OpenSpec input validation, package installation and full regression.
- Release a patch after implementation; retain #527 as deferred. Handle kaiwu's distinct #531 lifecycle report in its own change before the next release.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-release-artifact`: patched locked validation dependency and compatibility proof.

## Impact

npm-shrinkwrap.json and bounded validation evidence. No new direct dependency, interface or permission change. OpenSpec schemas accept user-controlled arrays; reachability of the advisory's resource-exhaustion condition is not assumed from audit alone.
