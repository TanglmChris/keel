## Context

The shift feature is frozen except for bug fixes (owner, 2026-10-14); #343's owner decision was to keep everything (2026-10-18), and the found segments are a gap in it. The owner asked for this fix on 2026-10-18.

## Facts

- F1 — `keepEnded` (`src/core/chat/notice.js`) copies only the recorded segments `recordSegment` passes it; `claudeTranscripts` (`src/core/shift.js`) finds the bound worktrees' transcripts at `history` time and records none.
- F2 — `history` sets `kept` only from a record's `kept` field.
- F3 — keel-maint, 2026-10-18: 12 ended segments, 10 recorded and kept, 2 found (13.3 MB and 8.6 MB) unkept.

## Decisions

- D1 — `recordSegment`, after `keepEnded`, copies each found transcript not named by a record to `keptFile(role, transcript)` — unless a copy at least as new as it (by mtime) is already there, such as one made by hand — and records it, still marked found, with its `kept` and `kept_from`. A found transcript is therefore read once, when first recorded; afterwards `keepEnded` refreshes its copy like any other ended segment, and `history` lists it from the record once the host's file is gone, since a scan finds only files that exist. Scheduled runs stay out, as `history` leaves them out, and the current segment stays last in the record.
- D2 — `history` takes a segment's copy from its record or, failing that, from `keptFile(role, transcript)` when it exists, so a copy made by hand before this fix is read too.
