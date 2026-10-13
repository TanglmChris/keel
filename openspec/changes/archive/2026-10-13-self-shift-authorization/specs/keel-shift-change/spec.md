## MODIFIED Requirements

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it. In the Claude desktop app, which Keel recognises by `CLAUDE_CODE_ENTRYPOINT=claude-desktop` together with a non-empty `CLAUDE_CODE_HOST_SESSION_ID`, a clear starts no session until a prompt arrives. There, `ready` MUST record the desktop session id in the note, and `ready --wake` MUST NOT say the waiter wakes the new session. Its output MUST instead give these steps in this order: turn Remote Control off and wait for that call to return; only then create a one-shot scheduled task with `create_scheduled_task`, whose prompt calls `send_message` to that session id with the resume instruction, which asks the woken session to restore Remote Control and its title as `keel shift resume` says, saying that a task created earlier can fire first and get the clear refused; rename the outgoing session with `set_session_title` so its archived copy can be told apart; and call `clear_session("self")`. When `authorize:` declares `self-shift`, the output MUST say the repository standing-authorizes these four steps, so the session takes them without asking; otherwise it MUST name `self-shift` as the declaration that would. The output MUST name the `permissions.allow` entry `mcp__ccd_session_mgmt__set_remote_control` and the `authorize:` entry `shift-restore` that an unattended restore needs, and MUST NOT give approval of `clear_session` as a reason. Keel MUST NOT create the task.

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
- **THEN** the first note records `Desktop session: local_test-319`, and its output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control`, `set_session_title`, `mcp__ccd_session_mgmt__set_remote_control` and `shift-restore`, names turning Remote Control off before `create_scheduled_task`, and neither says `The wake is armed` nor names `mcp__ccd_session_mgmt__clear_session`; the second output says `The wake is armed` and names neither `send_message` nor `create_scheduled_task`

#### Scenario: A declared self-shift lets the session take the four steps without asking
- **WHEN** `dev` runs `keel shift ready --wake "…"` in the desktop app, once with `authorize:` declaring `self-shift` and once without
- **THEN** the first output says `Standing-authorized by \`self-shift\``, and the second names `self-shift` as the declaration that would, without that sentence
