## Why

Issue #347 (rtl_ppa_prj, TanglmChris/rtl_ppa_prj#311): shift notes go stale between `keel shift ready` and `keel shift resume`, and the next shift acts on them as current. A note said "A84 待合入" (waiting to be merged) when that commit was already in `origin/main`, and the coordinator corrected the cold start by hand. Notes there routinely cite `<branch> @ <sha>` and commit ids.

## What Changes

- `keel shift resume` lists, after the note, each commit id and `<branch> @ <sha>` the note names, checked against the remote-tracking refs: already in the default branch, branch moved (with its new tip), branch gone, or not found.
- It fetches nothing and says so, naming when the refs were last fetched.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: a resumed note's commits are checked against the remote.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
