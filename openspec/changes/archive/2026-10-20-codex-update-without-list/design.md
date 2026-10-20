## Context

`updateCodexPlugin` in `bin/keel.js` calls `codexKeel()` up to three times, and each call runs `codex plugin list --json`:
- before the update, to learn whether Keel is installed, the marketplace and its source type, and the version;
- after the marketplace upgrade, to find the new install path for the hook comparison;
- after `plugin add`, to report the new version.

A failed first query returns `failed` before any step runs.

## Facts

- F1 — #412: the list query hung for more than 90 seconds while the upgrade itself took 35 seconds. The owner's `~/.codex/config.toml` has:

  ```toml
  [marketplaces.keel-marketplace]
  source_type = "git"
  source = "https://github.com/TanglmChris/keel.git"
  ref = "main"
  sparse_paths = [".agents/plugins", "plugins/keel"]
  ```

  The cache is at `~/.codex/plugins/cache/keel-marketplace/keel/<version>/`.
- F2 — The existing code already reads `$CODEX_HOME/plugins/cache/<market>/keel/<version>/hooks/codex.json` to compare hooks, so the cache layout is something Keel already depends on.
- F3 — The `update-host-query-timeout` scenario runs with an empty `CODEX_HOME`. Its assertion that no Codex command runs after a failed query therefore still holds under D1.

## Decisions

- D1 — `codexKeelFromDisk(market)`:
  - Reads the `[marketplaces.<market>]` section of `$CODEX_HOME/config.toml` for `source_type`.
  - Reads the version directories under `$CODEX_HOME/plugins/cache/<market>/keel/` and takes the highest by numeric comparison.
  - Returns an install record with `fromDisk: true` only when both exist. Otherwise it returns null, and the failure is reported exactly as before.
  - The market is `keel-marketplace`, the name Keel installs under; with the list unavailable there is nothing else to read it from.
- D2 — With a disk record, every later `codexKeel()` call in that run is replaced by the disk read, because a query that just hung would likely stall again. The line appends: "`codex plugin list --json` did not answer (<reason>); versions read from <cache dir>".
- D3 — A non-Git source on disk is reported `manual`, exactly as a listed one is.
