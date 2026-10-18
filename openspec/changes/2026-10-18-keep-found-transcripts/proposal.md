## Why

Issue #361: 5.143.0 (#343) copies a role's ended transcripts when its next segment starts, but only the segments the hooks recorded. `keel shift history` also lists, as `(found)`, the Claude transcripts of the role's bound worktrees that no record names — the conversations from before segments were recorded (#304) — and those were never copied. `history` also reads a copy only through a segment record, so a copy of a found transcript is invisible to it. On 2026-10-18 keel-maint had 10 recorded segments kept and 2 found ones (22 MB) unkept; the owner had them copied by hand and asked for the fix.

## What Changes

- At a segment change the hook also copies each found transcript of the role's bound worktrees that has no copy at least as new as it, leaving out scheduled runs and the current transcript, into the same `shift/transcripts/<role>/<name>.gz`.
- `history` uses that path for any segment whose record names no copy, so a found segment whose file is gone reads `(kept)` and `--grep` searches the copy.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: found transcripts are kept, and a copy at the kept path is read without a record.

## Impact

`src/core/chat/notice.js`, `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/shift-change.md`, one published spec, the changelog.
