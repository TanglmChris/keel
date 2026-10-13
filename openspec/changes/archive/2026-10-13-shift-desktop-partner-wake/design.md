## Context

Issue #319, its two live-test comments of 2026-10-13, and the owner's decision of the same day: partner wake, printed by `keel shift ready`, with Keel launching nothing (D7 of #293). Not chosen: only correcting the wording (it leaves an unattended desktop self-shift stuck); a standing coordinator session (a second session to keep alive). Out of scope: a coordinator's `keel shift start` for a role cleared on the desktop app. Whether a chat record wakes a cleared desktop session there has not been tested, so it goes to its own issue.

## Facts

- F1 — In the desktop app, Claude Code sessions carry `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=<local_…>`, the id the app's `send_message` and `set_remote_control` take (observed 2026-10-13, app 2.31226.1).
- F2 — After `clear_session("self")`, no new transcript appears until a prompt arrives (#319 evidence, 07:20–07:22).
- F3 — A one-shot scheduled task `keel-maint-shift-wake-test` fired at 00:42:18Z; its `send_message` started the cleared session at 00:42:26Z with `session_source: startup` (#319 comment 6135465431).
- F4 — The woken session came back with Remote Control off, although `connect_new_sessions_to_remote_control` is On. Its `set_remote_control("self", true)` was refused by the auto-mode classifier until the owner added `mcp__ccd_session_mgmt__set_remote_control` to `permissions.allow` (#319 comment 6136073139).

## Decisions

- D1 — Keel treats a run as the desktop app exactly when `CLAUDE_CODE_ENTRYPOINT` is `claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID` is non-empty. It reads the environment and calls no host tool.
- D2 — `ready` in the desktop app writes `Desktop session: <id>.` into the note head, whether or not `--wake` is given.
- D3 — `ready --wake` in the desktop app still arms the waiter. Its record is the chat-side copy of the instruction, and it is harmless once a session exists. In the clear hint, the line `The wake is armed: once …` is replaced by:
  `On the Claude desktop app a clear starts no session until a prompt arrives, so the waiter alone wakes nothing (#319). Before you clear, create a one-shot scheduled task with the host's \`create_scheduled_task\`, firing a few minutes after the clear, whose prompt calls \`send_message\` to session \`<id>\` with: "<role>: your new shift starts now. First turn Remote Control back on with set_remote_control(\"self\", true), then run \`keel context\` and \`keel shift resume\`." Keel creates no task. Turning Remote Control back on unattended needs \`mcp__ccd_session_mgmt__set_remote_control\` in \`permissions.allow\`.`
- D4 — `keel shift resume` in the desktop app, when it prints a note, appends `On the Claude desktop app Remote Control does not survive a clear: turn it back on with \`set_remote_control("self", true)\`.`
- D5 — Outside the desktop app every output is unchanged. The test environment strips both variables, so the existing scenarios run the same on any host.
- D6 — Both shift-change docs give the desktop recipe in the `--wake` paragraph, and say Remote Control must be restored after the clear.
