## Why

Issue #307, part 1 (2026-10-12): after a day of a host-run patrol in rtl_ppa_prj, the owner moved routine coordination into it — the patrol nudges each role's session itself, and a routine shift change no longer goes through the coordinator. The project did it with a hand-written prompt that sends host messages by session id and keeps its own rate limits; its first version nudged a role over week-old group chatter. Owner decision, 2026-10-12: nudges are `keel chat` direct messages from `keel-patrol`, Keel keeps the rate limits, and a self-initiated shift is one filed with `ready --wake`.

## What Changes

- `keel patrol --nudge` checks every bound role other than the patrolling one, and nudges an idle role with one direct message from `keel-patrol` in three cases:
  - Something addressed to the role has waited longer than `--idle`. At most once per two hours.
  - The host reports, through `--context <role>=<percent>`, that the role's context is at or above `--shift-at` (default 50). The message tells the role to change its own shift with `ready --wake`. At most once per six hours.
  - A self-initiated shift note has waited longer than `--idle` and no wake reached the role. Once per note.
- Records from Keel's own senders never count as waiting.
- `keel shift ready --wake` marks the note as self-initiated; a note filed without it is never nudged to resume.

## Capabilities

### Modified Capabilities
- `keel-coordinator-patrol`: the patrol nudges idle roles directly.

## Impact

`src/core/patrol.js`, `src/core/shift.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
