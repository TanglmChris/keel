## MODIFIED Requirements

### Requirement: Shift state is visible

`keel shift status` MUST list, for each role with a shift record or note, whether a request is open, a note waits, or the role resumed, with times. A waiting note that records a `Desktop session:` and was written longer ago than the overdue time — 15 minutes, which `KEEL_SHIFT_WAKE_OVERDUE_MS` overrides — MUST be listed as an overdue desktop wake naming that session id, `list_task_runs`, and `send_message`; a younger one, or one recording no desktop session, MUST NOT.

#### Scenario: Status follows the steps
- **WHEN** `rtl` has requested a shift change of `verify`, and `verify` is ready
- **THEN** `keel shift status` lists `verify` with a waiting note

#### Scenario: An overdue desktop wake is flagged
- **WHEN** `verify` runs `keel shift ready --wake` in the desktop app with session `local_test-319`, and `keel shift status` runs once with the overdue time far away and once with it passed
- **THEN** the first output does not say `overdue`, and the second says `overdue` and names `local_test-319`, `list_task_runs` and `send_message`

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it. In the Claude desktop app, which Keel recognises by `CLAUDE_CODE_ENTRYPOINT=claude-desktop` together with a non-empty `CLAUDE_CODE_HOST_SESSION_ID`, a clear starts no session until a prompt arrives. There, `ready` MUST record the desktop session id in the note, and `ready --wake` MUST NOT say the waiter wakes the new session. Its output MUST instead give these steps in this order, and MUST NOT tell the session to turn Remote Control off: create a one-shot scheduled task with `create_scheduled_task`, whose prompt first calls `get_session` on that session id and, when it reports the session archived, calls `unarchive_session` on it, then calls `send_message` to it with the resume instruction, which asks the woken session to restore Remote Control and its title as `keel shift resume` says, and, if that send is still refused because the session is archived, unarchives it and sends once more, saying which path it took, and treats a send result of `delivered` or `queued` as a delivered wake and any other result, after that retry, as a failed wake, for which it calls `PushNotification` naming the session and the result and starts its reply with `WAKE FAILED`; the output MUST say that the app's auto-archive can archive the cleared session before the wake and that unarchiving brings back its worktree, MUST NOT tell the session to dismiss its bound PRs, MUST say that a task which fires before the clear gets the clear refused, so the next two steps follow at once, and MUST say that Remote Control stays on across the clear and the app reconnects it under a new address that a remote viewer has to open; rename the outgoing session with `set_session_title` so it reads as between shifts until the woken session renames it back, without calling it an archived copy; and call `clear_session("self")`. When `authorize:` declares `self-shift`, the output MUST say the repository standing-authorizes these three steps, so the session takes them without asking; otherwise it MUST name `self-shift` as the declaration that would. The output MUST name the `permissions.allow` entries `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session` and the `authorize:` entry `shift-restore` that an unattended restore needs, and MUST NOT give approval of `clear_session` as a reason. Keel MUST NOT create the task.

#### Scenario: The cleared session is woken once
- **WHEN** `dev` runs `keel shift ready --wake "…"`, a SessionStart with source `compact` follows, and then one with source `clear`
- **THEN** no wake record exists after the `compact` start, and after the `clear` start `dev` has one unread record from `keel-shift` naming `keel shift resume`, and `keel chat notice --check` for `dev` exits 0

#### Scenario: A role without a coordinator is told how its new session starts
- **WHEN** a role that no request named runs `keel shift ready` without `--wake`
- **THEN** the output says nobody is set to start the new session and names `--wake`

#### Scenario: A host run's start does not wake the role
- **WHEN** `dev` runs `keel shift ready --wake "…"`, a session starts in `dev`'s worktree with source `startup`, and its first prompt starts with `<scheduled-task`
- **THEN** no wake record exists after the settle time, and a later `clear` start still wakes `dev` once

#### Scenario: A desktop self-shift is told how its next session gets started
- **WHEN** `dev` runs `keel shift ready --wake "…"` with `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=local_test-319`, and runs it again without those variables after resuming
- **THEN** the first note records `Desktop session: local_test-319`, and its output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control`, `set_session_title`, `mcp__ccd_session_mgmt__set_remote_control` and `shift-restore`, does not name `set_remote_control("self", false)`, names `create_scheduled_task` before `set_session_title` and `set_session_title` before `clear_session`, names `get_session` before `unarchive_session` and `unarchive_session` before `send_message`, names `delivered`, `PushNotification` and `WAKE FAILED`, names `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session`, and neither says `The wake is armed`, `archived copy` nor names `unbind_pr`, `get_status` or `mcp__ccd_session_mgmt__clear_session`; the second output says `The wake is armed` and names none of `send_message`, `create_scheduled_task`, `unbind_pr` and `unarchive_session`

#### Scenario: A declared self-shift lets the session take its outgoing steps without asking
- **WHEN** `dev` runs `keel shift ready --wake "…"` in the desktop app, once with `authorize:` declaring `self-shift` and once without
- **THEN** the first output says `Standing-authorized by \`self-shift\``, and the second names `self-shift` as the declaration that would, without that sentence
