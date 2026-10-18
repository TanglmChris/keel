## Why

Issue #365: on 2026-10-18, after the 5.145.0 release, `keel --update` twice reported `codex plugin: failed - \`codex plugin list --json\` timed out after 30 s` on the owner's proxied link; the same query run directly took 58.2 s, and 15 minutes later 1.21 s and 0.89 s. The query is usually about a second and occasionally about a minute, so the 30 s limit from #354 turns each slow spell into a missed Codex update that needs a manual rerun.

## What Changes

- A `plugin list --json` query that times out is retried once with the same limit before the component reads `failed`; the line then says it timed out twice. A query that exits nonzero or prints no JSON is not retried.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: a timed-out host query is retried once.

## Impact

`bin/keel.js`, `scripts/validate_plugin.py`, `docs/updating.md`, one published spec, the changelog.
