## Why

5.152.0 (#347) lists the commits a resumed shift note names, reading a commit id as 7–40 hex digits with at least one letter and one digit so a date is not one. About 2% of short shas are all digits, and those were skipped — including after `@`, where the pair already says it is a commit. CI hit it on 2026-10-19 (`'feat @ 02607471' is not marked 'branch moved…'`, run 39211624782), which made `shift-resume-checks-commits` fail at random.

## What Changes

- After `@` in `<branch> @ <sha>`, any 7–40 hex digits are a commit id.
- A bare all-digit token is listed when it resolves to a commit, so a date that resolves to nothing is still not listed.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: an all-digit sha is still a commit.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
