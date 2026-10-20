## Why

Issue #412. On 2026-10-20 (codex-cli 0.163.0, Keel 5.170.0), `codex plugin list --json` hung for more than 90 seconds, and `keel --update` reported the Codex plugin `failed` on two runs. In the same minute, `codex plugin marketplace upgrade keel-marketplace` succeeded by hand in 35 seconds and brought the cache to 5.170.0. Only the query was stuck, yet Keel gave up the update with it. The hang is intermittent; the same query answered in about 1 second later that afternoon (#354, #365).

## What Changes

- When `codex plugin list --json` fails, `keel --update` reads Codex's own state instead of giving up:
  - the marketplace source from `[marketplaces.keel-marketplace]` in `$CODEX_HOME/config.toml`;
  - the installed version from `$CODEX_HOME/plugins/cache/keel-marketplace/keel/<version>/`.
- If that state shows Keel installed from a Git marketplace, the upgrade and `plugin add` run as usual. Versions before and after are read from the cache, and the line says the list query did not answer.
- If the state shows no Keel install, the line still reads `failed`, as #354 decided: a failed query is never reported as `absent`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: a hung Codex query no longer stops an update Codex's own state can carry.

## Impact

`bin/keel.js` (`updateCodexPlugin`), `scripts/validate_plugin.py`, the published spec, the changelog.
