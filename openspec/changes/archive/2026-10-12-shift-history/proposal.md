## Why

Issue #304 (2026-10-12): a shift change clears the session. The old conversation stays on disk as its own transcript file, but nothing points at it — the host's transcript search and event reader cover only the current segment — so a previous shift's reasoning is effectively lost. The host also refuses to clear a session serving Remote Control, which most rtl_ppa_prj sessions do, and Keel's clear hint does not say so. Owner decision, 2026-10-12: keep clearing, and record each shift's transcript so it can be found again.

## What Changes

- The chat hooks of a session bound to a role record each transcript file it runs in, with when it started and when the next one replaced it, under the role's shift records. A host-run session's record is undone with the rest of its effects.
- `keel shift history [<role>] [--grep <text>] [--json]` lists those segments and the role's past shift notes, newest first, and with `--grep` prints matching lines from the transcripts.
- `keel shift ready` says the shift's conversation stays findable through `keel shift history`, and the clear hint says to turn Remote Control off before clearing.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: a cleared shift's conversation stays findable.

## Impact

`src/core/chat/notice.js`, `src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
