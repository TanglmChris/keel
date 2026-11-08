## Why

Issue #510, opened 2026-11-08 from the owner's choice of candidate 5 in #508 ("按推荐走"; ordered by keel-maint at the owner's request the same day). After the macOS upgrade the two `dev.keel.tick.*` launchd jobs were not loaded and `keel tick` did not run from 2026-11-07 11:46 for about 23 hours; `keel --doctor` reported ok throughout because it checks a job's node and directories, not whether it runs. A tick that does not run cannot report that it does not, so something must read the trace it leaves.

The owner's boundary (2026-11-08, #508): Keel registers nothing on the host and does not call `launchctl`. The trace therefore has to be in the repository's own state.

## What Changes

- **`keel tick` records `last_tick` in `tick/state.json` on every run**, including a run where the patrol is not due. Today the file holds only the patrol's `last_run`, once an hour.
- **`keel --doctor` reports the tick's heartbeat**: `tick` ok with the time of the last run; a problem when the last run is more than 15 minutes old, naming the time and how to repair (re-run the install commands `keel tick task` prints); a problem when the repository declares `runner: tick` and no run was ever recorded.
- **The SessionStart context says so too**, as one extra line, only when the heartbeat is stale or never recorded, so a session starts knowing its tick is silent. `keel context --json` carries `patrol.tick`.
- A repository that declares no tick and has no recorded run is not checked.
- Not changed: tick's wake, hand-over and patrol behavior; nothing reads `~/Library/LaunchAgents` or calls `launchctl` (the existing doctor check of the plist stays as it is).

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/tick.js`, `src/core/context.js`, `bin/keel.js`, `plugins/keel/scripts/session-start.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog.
