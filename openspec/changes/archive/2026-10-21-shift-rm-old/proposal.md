## Why

Issue #418. On 2026-10-20 the owner said: "keel 老的 session 虽然有时间区分，但没有 stop 标记，还是容易看错，我建议老的要 stop 掉；这是个通用流程问题".

Since 5.168.0 a hand-over stops the old shift's session but leaves it listed. Its name differs from the current shift's only by the time. On 2026-10-21 the owner compared three probes in the claude.ai, desktop, and phone session lists:
- a stopped session;
- a session disconnected from Remote Control and then stopped;
- a session stopped and then removed with `claude rm`.

Only the removed one was told apart: it no longer appears. The owner chose that.

The shift feature is frozen (10-14); this is an owner-requested exception.

## What Changes

- **`shift: keep_old_sessions:` defaults to 0 instead of 3.** After a delivered hand-over, every stopped session of the role is removed with `claude rm`, the one just handed over included. The existing mechanism does the removal, and only once Keel's store holds its transcript. `keel shift history <role> --show <id>` still prints each removed shift in full. A repository that wants old shifts listed declares a number.
- **`keel shift ready --wake` in a CLI session** says the old session will be removed and how to read it, instead of `claude attach`, when nothing is kept.
- **`shift` joins `CONFIG_DECLARATIONS`.** It was read by `src/core/config.js` and documented only in `docs/cli-team.md`. `keel/config.yaml` documents it like every other declaration.
- **`docs/cli-team.md` and its Chinese page** state the new default.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

The change touches:
- `src/core/config.js`, `src/core/shift.js`;
- `keel/config.yaml`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`;
- `scripts/validate_plugin.py`, the published spec, and the changelog.

A repository with old shift sessions listed sees them removed at its next hand-over, each only after Keel holds its transcript.
