## Why

Issue #295 (2026-10-12): the coordinator's patrol ran as a cron inside the coordinator's own session — expensive, and lost on every clear until someone rebuilt it. rtl_ppa_prj moved it by hand to a desktop scheduled task on a small model, which survives clears, and found that an hourly patrol must report only what changed, or it wakes the coordinator every hour for nothing. The owner decided on 2026-10-12: Keel renders the host task and the model installs it; the change-based logic moves into `keel patrol`; `patrol:` names the host task, and no generic scheduler is added.

## What Changes

- `keel patrol --since-last` keeps a snapshot per role — shift status, the remote default branch tip, the main checkout's uncommitted files, each role's idleness and open todos, and the role's waking unread records older than `--idle` — reports only what differs from the previous run, and exits 2 only when something did. The first run records a baseline and reports nothing.
- `--notify` (with `--since-last`) sends those changes to the patrolling role as one direct message from `keel-patrol`, which wakes its session, so a scheduled run needs no model judgment and no session id.
- `patrol:` accepts `host_task:` (the host scheduled task's id) and `model:` (passed through, never chosen by Keel). With `host_task:` declared, the reminder says the host task runs the patrol and outlives the session, and asks to confirm it is still enabled instead of re-creating a session schedule.
- `keel patrol task` prints the host scheduled task to install: its id, a suggested cron from `every:`, the declared model if any, and a self-contained prompt that runs `git fetch` and `keel patrol --since-last --notify` against the coordinator's worktree by path.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: change-based patrol, a notice to the coordinator, the host-task declaration, and the rendered task.

## Impact

`src/core/patrol.js`, `src/core/config.js`, `src/core/context.js`, `src/core/shift.js`, `plugins/keel/scripts/session-start.js`, `keel/config.yaml` comments, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
