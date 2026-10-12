## Why

Issue #307, part 2 (2026-10-12): the owner's rule for the weekly quota is to say nothing at 50 %, to report once each when it crosses 90 %, 95 %, and 99 % in a quota period, and at 90 % or more to stop the patrol's nudges, which wake large sessions, and report only to the coordinator. Keel cannot see the quota; the host-run task can. Owner decision, 2026-10-12.

## What Changes

- `keel patrol --quota <percent>` takes the host's weekly usage figure.
- Each threshold in `--quota-alerts` (default `90,95,99`) becomes a risk once per quota period. That risk reaches the coordinator through `--notify` (5.122.0).
- Keel keeps which thresholds it has reported, and starts over when the figure drops, which marks a new period.
- At or above `--quota-quiet-at` (default 90), `--nudge` sends nothing and says so.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: quota thresholds as risks, and quiet nudging near the limit.

## Impact

`src/core/patrol.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
