## MODIFIED Requirements

### Requirement: The new shift resumes from the note

While a note waits for the worktree's role, or for the worktree when it has no role, `keel context` and the SessionStart projection MUST include one line naming `keel shift resume`, without changing the context's status, selection, or next action. `keel shift resume` MUST print the note, move it to `keel-chat/shift/history/`, and, when the worktree has a role, post that the role is on shift to the coordinator of the latest shift request; after that the line MUST no longer appear; with no note waiting it MUST say so and exit 0. Run in the Claude desktop app, `resume` MUST, when it prints a note, also say to check Remote Control with `get_session` and turn it back on with `set_remote_control` only if it is off, and to rename the session back with `set_session_title`, because a clear there keeps no title and may leave Remote Control off; when `authorize:` declares `shift-restore` it MUST say that the repository standing-authorizes both, so the woken session acts without asking, and otherwise MUST name `shift-restore` as the declaration that would. Elsewhere it MUST NOT say any of this.

#### Scenario: The notice points to the note and resume consumes it
- **WHEN** a note waits for `verify`, the SessionStart projection runs in its worktree, and `verify` then runs `keel shift resume`
- **THEN** the projection names `keel shift resume`, the command prints the note text, the note moves to history, `dm-rtl--verify` gains an on-shift message, and the next projection no longer names it

#### Scenario: A resumed desktop shift is told to restore Remote Control
- **WHEN** a role resumes its note with `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID` set, and another resumes without them
- **THEN** the first output names `set_remote_control` and `set_session_title` and the second names neither

#### Scenario: A declared shift-restore lets the woken session restore without asking
- **WHEN** a role resumes its note in the desktop app, once with `authorize:` declaring `shift-restore` and once without
- **THEN** the first output says the repository standing-authorizes the restore, and the second names `shift-restore` as the declaration that would

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it. In the Claude desktop app, which Keel recognises by `CLAUDE_CODE_ENTRYPOINT=claude-desktop` together with a non-empty `CLAUDE_CODE_HOST_SESSION_ID`, a clear starts no session until a prompt arrives. There, `ready` MUST record the desktop session id in the note, and `ready --wake` MUST NOT say the waiter wakes the new session. Its output MUST instead give these steps in this order, and MUST NOT tell the session to turn Remote Control off: create a one-shot scheduled task with `create_scheduled_task`, whose prompt first calls `get_session` on that session id and, when it reports the session archived, calls `unarchive_session` on it, then calls `send_message` to it with the resume instruction, which asks the woken session to restore Remote Control and its title as `keel shift resume` says, and, if that send is still refused because the session is archived, unarchives it and sends once more, saying which path it took; the output MUST say that the app's auto-archive can archive the cleared session before the wake and that unarchiving brings back its worktree, MUST NOT tell the session to dismiss its bound PRs, MUST say that a task which fires before the clear gets the clear refused, so the next two steps follow at once, and MUST say that Remote Control stays on across the clear and the app reconnects it under a new address that a remote viewer has to open; rename the outgoing session with `set_session_title` so it reads as between shifts until the woken session renames it back, without calling it an archived copy; and call `clear_session("self")`. When `authorize:` declares `self-shift`, the output MUST say the repository standing-authorizes these three steps, so the session takes them without asking; otherwise it MUST name `self-shift` as the declaration that would. The output MUST name the `permissions.allow` entries `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session` and the `authorize:` entry `shift-restore` that an unattended restore needs, and MUST NOT give approval of `clear_session` as a reason. Keel MUST NOT create the task.

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
- **THEN** the first note records `Desktop session: local_test-319`, and its output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control`, `set_session_title`, `mcp__ccd_session_mgmt__set_remote_control` and `shift-restore`, does not name `set_remote_control("self", false)`, names `create_scheduled_task` before `set_session_title` and `set_session_title` before `clear_session`, names `get_session` before `unarchive_session` and `unarchive_session` before `send_message`, names `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session`, and neither says `The wake is armed`, `archived copy` nor names `unbind_pr`, `get_status` or `mcp__ccd_session_mgmt__clear_session`; the second output says `The wake is armed` and names none of `send_message`, `create_scheduled_task`, `unbind_pr` and `unarchive_session`

#### Scenario: A declared self-shift lets the session take its outgoing steps without asking
- **WHEN** `dev` runs `keel shift ready --wake "…"` in the desktop app, once with `authorize:` declaring `self-shift` and once without
- **THEN** the first output says `Standing-authorized by \`self-shift\``, and the second names `self-shift` as the declaration that would, without that sentence
