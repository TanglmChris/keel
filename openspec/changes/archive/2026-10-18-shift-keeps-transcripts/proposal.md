## Why

Issue #343 (owner, 2026-10-15): keep the full text of each shift's session. Today `keel shift history` lists each shift's transcript by path, and the file stays where the host keeps it. Claude Code deletes transcripts older than `cleanupPeriodDays` (default 30; unset on this machine), so the oldest keel-maint segment still listed (2026-10-13) goes around 2026-11-12, after which `history` prints `(missing)` and `--grep` finds nothing. The shift feature is frozen to bug fixes; this is the owner's explicit exception.

## What Changes

- When a role's session starts a new transcript, the chat hook copies every ended segment of that role — the one just ended and any earlier one not yet copied or grown since — into Keel's store as gzip-compressed JSONL, `<git common dir>/keel-chat/shift/transcripts/<role>/<transcript name>.gz`. It stays on this machine: the archive branch syncs `groups`, `cursors`, `members` and `presence` only. Everything is kept; there is no cap (owner, 2026-10-18).
- `keel shift history` reads Keel's copy when the host's file is gone, says which it read, and `--grep` searches it.
- Codex is covered by the same hook: its hooks pass the rollout file as `transcript_path` (measured), and `--grep` now reads Codex's rollout message records as well as Claude's.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: a cleared shift's conversation is kept, not only pointed at.

## Impact

`src/core/chat/notice.js`, `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/` shift docs if they describe history, one published spec, the changelog.
