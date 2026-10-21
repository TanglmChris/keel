## Why

Issue #424. On 2026-10-20, in the kaiwu-lead session, the owner said: "我每个去跑 reload 太麻烦了"; "或换班更新". After a release, every running Claude background session keeps the skills it loaded until someone types `/reload-plugins` in it. That day four releases shipped, and eleven background sessions were listed.

Measured on 2026-10-21:

**A CLI hand-over already adopts the new plugin.** Since 5.168.0 it starts a new process. The skill listing in the transcripts shows this:
- kaiwu-lead `0e12b6cb` started on 5.170.0 and lists the retired `keel:keel-run-single-task-goal`;
- `ef20932c`, which a hand-over started after 5.175.0 was installed, does not.

The issue's premise that a CLI shift is an in-process `/clear` came from the stale Chinese shift page, corrected in 5.177.0.

**A session that does not change shift keeps the old plugin.** Restarting it adopts the installed one. Measured on a probe started on 5.177.0, after 5.178.0 was installed:
- `claude stop`, then `claude --bg --resume <id> "/compact"`, ran the SessionStart hooks of 5.178.0 with no "in place of the loaded" line;
- `claude --bg --resume <id>` with no prompt starts the process idle, writes no turn, and calls no model.

## What Changes

**`keel --update --adopt` restarts the idle background sessions started before the installed plugin's `lastUpdated`.** For each one it:
- runs `claude stop`;
- waits for the process to exit;
- runs `claude --bg --resume <session id>` with no prompt.

Everything else about the session stays the same: the session id, its worktree, its chat role, and its conversation. It does not touch:
- busy or waiting sessions;
- sessions whose worktree has an active write guard;
- the session running the command.

Each of these is named, to adopt at its next shift or a later `--adopt`.

**`keel --update` without `--adopt` names the older sessions** and says that `--adopt` restarts the idle ones. It prints nothing when there are none.

**`docs/updating.md` and both READMEs** state this:
- a CLI hand-over adopts the new plugin;
- `--adopt` covers sessions that do not change shift.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`

## Impact

`bin/keel.js`, `docs/updating.md`, `README.md`, `README.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog. Desktop and Codex sessions are unchanged: a desktop session is not a background session, and Codex re-resolves its plugin at every hook.
