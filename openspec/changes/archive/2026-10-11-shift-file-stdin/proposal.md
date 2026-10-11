## Why

Issue #261: on 2026-10-06, under 5.99.1, the Keel maintenance session ran `keel shift ready --file - <<EOF … EOF` while changing shift. It got `ENOENT: no such file or directory, open '-'` from `readNoteText` as an uncaught error with a Node stack trace. Giving the note on stdin without `--file` already worked.

## What Changes

- `keel shift ready --file -` reads the note from stdin, following the usual convention.
- A `--file` that cannot be read is refused as a `keel shift:` error naming the path. It is no longer an uncaught exception.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: `ready` takes `--file -` as stdin and refuses an unreadable `--file` by name.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
