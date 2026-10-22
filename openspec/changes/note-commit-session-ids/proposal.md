## Why

Issue #445, approved by the owner on 2026-10-21 as a bug fix under the shift freeze. When `keel shift resume` checks the commits a note names (#347), it reads session ids as commits. Keel writes such an id itself, in the note header `CLI session: <uuid>.`. So every CLI-era resume prints a false `not found`. This shift's resume printed `- b5a55cf2: not found` for the previous session's id.

A read-only survey of the 19 keel-maint notes found false `not found` lines in 5 of the 6 notes written since the check exists. The 10-20T1317 note has five, from session ids quoted in prose. A false alarm on every resume teaches the reader to skip the list. Separately, an empty `Desktop session:` slot leaves blank lines in every CLI note's header.

## What Changes

- **A session id is not a commit.** The first segment of a UUID is not read as a commit id. Neither is a token that begins a session id Keel has recorded: a `sessions/` record or a kept shift transcript. A hex token that is neither is still checked, and still reported `not found` when it resolves to nothing.
- **The note header has no blank lines for empty slots.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
