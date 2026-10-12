## Why

Issue #307, part 3 (2026-10-12): once the patrol nudges roles itself, what remains for the coordinator is risk — a shared checkout left dirty, low disk, a role that ignores its nudges, and the quota (part 2). Shift-status changes and new commits, which `keel patrol --since-last --notify` sends today (5.115.0), are mostly the coordinator's own doing and wake it for nothing. The owner also wants every run to leave one line in a log, so silent runs can be audited. Owner decision, 2026-10-12.

## What Changes

- `--notify` sends the coordinator only risks:
  - The primary checkout gaining uncommitted paths after a clean run.
  - A host-reported `--disk-free-gb` dropping below `--disk-min-gb` (default 20).
  - A role that has left two unread nudges in a row unanswered.
- Changes are still printed as `changed:` lines; risks are printed as `risk:` lines.
- Every `keel patrol` run appends one line to `patrol/log/<role>.log` in the chat store.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: `--notify` escalates only risks, and every run is logged.

## Impact

`src/core/patrol.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
