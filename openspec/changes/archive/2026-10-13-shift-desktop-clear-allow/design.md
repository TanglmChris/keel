## Context

#319 end-to-end test, its comment 6138487679, and the owner's decision of 2026-10-13. Not chosen: keeping the approval and having the owner approve each shift by hand, which is not unattended. Also not chosen: a wake that first checks the target was cleared, because the clear would still wait for an absent owner.

## Facts

- F1 — `clear_session("self")` called 02:41:17Z returned 02:54:23Z, and the call at 02:59:40Z returned 04:40:18Z. Both were refused with "a message the user sent is waiting to run after this turn, and a clear would erase it" (session transcript 76cdd21d…).
- F2 — The wake tasks fired at 02:45Z and 03:04Z, and their `send_message` was enqueued in the uncleared session after each refusal (transcript `queue-operation` entries 02:55:15Z, 04:41:01Z).

## Decisions

- D1 — The desktop partner step's last sentence reads: `Unattended, this needs two \`permissions.allow\` entries: \`mcp__ccd_session_mgmt__set_remote_control\` to turn Remote Control back on, and \`mcp__ccd_session_mgmt__clear_session\`, because a clear left waiting for approval lets the wake arrive first and the app then refuses it.`
- D2 — Both shift-change docs name `mcp__ccd_session_mgmt__clear_session` in the desktop recipe with the same reason.
