## Why

Issue #356 (rtl_ppa_prj coordinator `iecc-pm`, 2026-10-18): `keel patrol task` renders a fixed cadence (`every: 60m`), but the right cadence depends on what is going on, and the patrol output already holds what is needed to judge it. That day 140 runs fired hourly; during long waits and overnight most only recorded presence flips, while an hour is too slow once a risk shows up. The project wrote its own adaptive rules into its host task, and every project would repeat them. The owner chose, on 2026-10-19 after the team moved to background CLI sessions, one model-free CLI waker (`keel tick`) that will run the patrol on this recommendation; this change is the recommendation.

## What Changes

- `keel patrol` prints `next: <duration> (<rule>)`, and `--json` adds `next_after_s`, `next_rule` and `next_at`.
- With `cadence: adaptive` under `patrol:`, the first matching rule picks the delay: `risk` (a risk this run, 30m), `quota` (`--quota` at 90% or more, 4h), `night` (inside `quiet:`, no risk: until the window ends), `busy` (another role active, or an open wait or todo whose assignee is active, 60m), `idle` (3h). `risk:`, `quota:`, `busy:`, `idle:`, `quiet:`, `min:` and `max:` override the defaults.
- Without `cadence: adaptive` the recommendation is `every:` with rule `fixed`, which is today's behaviour.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`: a patrol recommends its next run.

## Impact

`src/core/patrol.js`, `src/core/config.js`, `scripts/validate_plugin.py`, one published spec, the changelog. The re-arming runner is a later change (owner's CLI waker).
