## Why

Issue #397, after the owner saw several `keel-maint` rows in `claude agents` on 2026-10-20:

1. 5.166.0 (#395) waits for the old session's row to lose its `status` before resuming it for the rename, but the row loses it about 1.8 s before the process exits (measured), and a resume in that gap still starts a running copy.
2. Every CLI shift leaves one stopped session and nothing removes any, so the list grows by one row per shift. The owner chose to keep the most recent N per role, N declared in `keel/config.yaml`, default 3.
3. The owner wants the full content of a shift that is no longer listed: today `keel shift history` lists and greps transcripts but prints none.

## What Changes

- The hand-over waits for the old session's process (the pid its row showed before the stop) to exit before the rename resume.
- After a delivered hand-over, stopped background sessions in the role's bound worktrees beyond the newest `shift: keep_old_sessions:` (default 3) are removed with `claude rm`, each only once Keel's store holds a copy of its transcript.
- `keel shift history <role> --show <session id>` prints that shift's whole conversation, from the host's transcript or Keel's kept copy.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: the CLI hand-over waits for the old process and keeps a bounded number of old sessions; `keel shift history --show` prints a past shift.

## Impact

`src/core/shift.js`, `src/core/config.js`, `scripts/validate_plugin.py`, `docs/cli-team.md` and its zh-CN twin, `docs/shift-change.md`, `keel/config.yaml` comments, the published spec, the changelog.
