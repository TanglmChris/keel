## Why

Issue #401: keel-maint's 5.168.0 hand-over on 2026-10-20 removed 2b7acbb6, although `keep_old_sessions` 3 should have kept it. The third kept slot went to d6bedfc8, a background session that was never given a prompt and has no transcript. A session like that is counted as an old shift, and because it has no transcript it is never removed, so it holds a slot for as long as it is listed.

## What Changes

- Only a session with a conversation, meaning a transcript in the host's files or in Keel's store, counts toward `keep_old_sessions`. A session with neither is not counted and stays.
- A counted session that falls outside the kept ones is removed once Keel's store holds its copy. A session whose host transcript is already gone but whose copy Keel holds is removed too.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: CLI retention counts only sessions with a conversation.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md` and its zh-CN twin, the published spec, the changelog.
