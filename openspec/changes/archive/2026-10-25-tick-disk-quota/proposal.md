## Why

Issue #456, approved by the owner on 2026-10-25. `keel patrol` reports two repository-wide risks: free disk below a floor (`--disk-free-gb`, `--disk-min-gb`) and weekly quota crossing an alert step (`--quota`). It reports them only when its caller passes the numbers. `keel tick` passes neither, so a repository that moves its patrol from a host scheduled task to `keel tick` silently loses both risks.

That happened in kaiwu-ip on 2026-10-22. The coordinators became background CLI sessions, which cannot create host scheduled tasks, so the patrol moved to `dev.keel.tick.kaiwu-ip`. Since then no run has reported disk or quota. That machine has filled its disk before.

## What Changes

- **The tick measures free disk itself.** It reads the filesystem of each patrol's worktree, with no model involved, and passes `--disk-free-gb`. It also passes `--disk-min-gb`, from `disk_min_gb:` when a `patrol:` item declares one and the patrol's default of 20 GB otherwise.
- **The tick reads quota from a file the repository names** (owner, 2026-10-25). The tick runs no command. A `patrol:` item may declare `quota_file: <path>`, whose first number is the weekly quota percent; the owner's status line can write it from `rate_limits.seven_day.used_percentage`.
  - A fresh file is passed as `--quota`.
  - A file older than 6 hours, unreadable, or missing is not passed. The tick says so once, and again only when that state changes.
  - With no `quota_file:` declared, the tick says once that quota is not checked.
- **The risks still reach one coordinator.** The patrol already reports disk and quota only from the declaration that owns the repository-wide items (#434). The tick passes the numbers to every run, and the patrol decides.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/config.js`, `src/core/tick.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the README in both languages, the `keel/config.yaml` comment, the published spec, and the changelog.
