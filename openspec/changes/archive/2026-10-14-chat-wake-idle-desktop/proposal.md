## Why

Issue #331 (rtl_ppa_prj, 2026-10-13/14): on the Claude desktop app a role whose session is idle has no running Claude process, so nothing reads the chat record addressed to it. Todos to three idle roles sat unseen for about four hours; an hourly `keel patrol --nudge` nudged `iecc-design-sub` seven times while its unread count climbed and it never woke. One `send_message` to each session id woke it at once. The same cause was measured in #320 (a process-less desktop session saw no record for three minutes; `send_message` resumed it in 9 s). Today the coordinator must remember to follow every todo with a `send_message`, and each time it forgot, the todo waited for hours.

## What Changes

- A role's presence also records, when its session runs on the desktop app, that session's id and its Claude process id.
- `keel chat post`, `keel chat dm` and `keel chat todo` name, for each role the record wakes whose recorded desktop process is no longer running, the step that does wake it: `get_session`, `unarchive_session` when archived, then `send_message` to its session id. `--json` carries the same as `asleep`.
- `keel patrol --nudge`, when it nudges such a role, also reports a risk to the coordinator at once, naming the session id and the step, instead of waiting for two unanswered nudges.
- Keel still launches nothing and calls no host tool.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: presence records the desktop session, and posts name its wake step.
- `keel-coordinator-patrol`: a nudge to a process-less desktop session is a risk at once.

## Impact

`src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/patrol.js`, `scripts/validate_plugin.py`, the chat docs, two published specs, the changelog.
