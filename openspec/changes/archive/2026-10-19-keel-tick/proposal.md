## Why

On 2026-10-19 the agent team moved from the desktop app to background CLI sessions, where the desktop host scheduled tasks that ran the patrol (`rtl-ppa-pm-patrol`) can no longer reach the coordinator, and the project's own rule keeps the coordinator from holding a session-level cron. The owner chose one model-free CLI waker (`keel tick`) to run the patrol on the recommendation 5.153.0 added (#356), and asked that the CLI carry what is needed to keep it running.

## What Changes

- `keel tick [--repo <coordinator worktree>]` is one model-free step for a host scheduler such as launchd: when `patrol:` is declared and the last recommended `next_at` has passed (or none is recorded), it fetches `origin` and runs `keel patrol --since-last --notify` as the patrolling role, recording the new `next_at`; otherwise it says the patrol is not due and exits.
- `keel tick task` prints a launchd job that calls `keel tick` every 5 minutes, with the commands that install it, and creates nothing.
- `patrol: runner: tick` tells the coordinator's sessions that `keel tick` runs the patrol, instead of asking them to re-create a session schedule.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`: a host-run tick runs the patrol when due.

## Impact

`src/core/tick.js` (new), `bin/keel.js`, `src/core/config.js`, `scripts/validate_plugin.py`, one published spec, the changelog. Waking roles and the CLI self-shift follow in later changes.
