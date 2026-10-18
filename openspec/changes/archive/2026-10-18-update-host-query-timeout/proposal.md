## Why

Issue #354 (split from #329): on 2026-10-14 `codex plugin list --json` hung for minutes through the owner's proxy. `keel --update` runs every host call with a 5-minute limit, so each such query — two per Claude update, three per Codex update — can stall it for five minutes. Reading the code shows a second fault: `hostJson` returns null for a query that times out or fails, and the update then reports the host `absent` ("is not installed here or has no Keel plugin"), so a hang ends in a false statement. On 2026-10-18 (codex-cli 0.163.0) the query took 1.1–1.4 s and the hang did not reproduce.

## What Changes

- The read-only `plugin list --json` queries get a 30-second limit (owner, 2026-10-18); the update commands keep five minutes, since they download.
- A query that times out, exits nonzero, or prints no JSON reports that component `failed`, naming the command and why — for a timeout, the limit — and never `absent`. `absent` stays for a host whose executable does not resolve or that lists no Keel plugin.
- `KEEL_UPDATE_QUERY_TIMEOUT_MS` overrides the limit, like the existing `KEEL_UPDATE_CLAUDE`/`KEEL_UPDATE_CODEX`, so a test can trip it without waiting 30 s.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: a host query is bounded and its failure is not reported as an absent host.

## Impact

`bin/keel.js`, `scripts/validate_plugin.py`, `docs/updating.md`, one published spec, the changelog.
