# keel-shift-change Specification

## Purpose

A coordinated shift change for a role's session: requested by a coordinator, checked for loose ends, handed over through a transient note kept outside every worktree, and resumed by the new shift.

## Requirements

### Requirement: A coordinator requests a shift change and the role is woken

`keel shift request <role>`, run by a session with a chat role, MUST post a todo assigned to `<role>` in the direct group between the two roles, creating the group if absent, carrying the ref `keel-shift`, and so wake `<role>`. It MUST refuse a role equal to the requester's own.

#### Scenario: A request wakes the role
- **WHEN** `rtl` runs `keel shift request verify`
- **THEN** an open todo assigned to `verify` with ref `keel-shift` exists in `dm-rtl--verify`, and `verify`'s signal file was touched

### Requirement: The readiness check reports what would be lost or left running

`keel shift check`, run in a worktree, MUST report as items: uncommitted changes; commits reachable from HEAD that no remote-tracking ref contains, unless the repository has no remote, which it MUST report as a note rather than an item; an active write guard; processes whose working directory is inside the worktree, other than the checking process and its ancestors; linked worktrees other than the current and main ones that lie in a Claude scratchpad of a session started in this worktree, `claude-<uid>/<slug>/<session>/scratchpad/` with the slug being this worktree's path with each non-alphanumeric character turned into `-`, while it MUST report any other linked worktree under a temporary directory as a note naming its path; live `keel lock` leases this worktree holds; and, for the worktree's chat role, open todos assigned to it other than shift requests and unread records that would wake it. It MUST exit 1 when any item is present and 0 otherwise, change nothing, and with `--json` print the items.

#### Scenario: Each kind of loose end is reported
- **WHEN** the `verify` worktree has an uncommitted file, a commit not on its remote, `keel/guard.json`, a running process started in it, a linked worktree in a scratchpad of a session started in `verify`, a live `keel lock` lease, and an open todo assigned to `verify`
- **THEN** `keel shift check` exits 1 and names each of them

#### Scenario: A clean worktree is ready
- **WHEN** those are cleared
- **THEN** `keel shift check` exits 0

#### Scenario: Another session's temporary worktree does not block
- **WHEN** a linked worktree lies in the scratchpad of a session started in another directory, and nothing else is loose
- **THEN** `keel shift check` exits 0 and lists that worktree as a note

### Requirement: The outgoing shift leaves a note and closes the request

`keel shift ready` MUST run the readiness check and refuse while it reports items unless `--force-reason <text>` is given; MUST refuse an empty note; MUST store the note, taken from its text argument, `--file`, or stdin, in the repository's common directory, outside every worktree: at `keel-chat/shift/<role>.md` when the worktree has a chat role, and otherwise at `keel-chat/shift/worktree/<name>-<id>.md` for the worktree; MUST read stdin when `--file` is `-`; MUST refuse a `--file` it cannot read with an error naming the path and exit 1, without an uncaught exception; MUST, in a worktree with no chat role and without `--role`, be refused unless `--force-reason` is given, naming `keel chat role --set` and `--wake` and storing nothing, because nothing wakes the session that follows a clear there; MUST, when it stores such a note, record the reason in it as who starts the new session; MUST, when the worktree has a role, close the open shift request addressed to it with a reply opening `done`; and MUST print how to clear the session without clearing it.

#### Scenario: Ready is refused while loose ends remain
- **WHEN** `keel shift ready "note"` runs in a worktree the check reports items for
- **THEN** it exits non-zero, names the items, and stores no note

#### Scenario: Ready stores the note and closes the request
- **WHEN** the worktree is clean and `verify` runs `keel shift ready "next: rerun R007 on 1b64e8c"`
- **THEN** the note file holds that text, the request todo is done, and the output names `clear_session` and `/clear`

#### Scenario: A worktree without a chat role is pointed to a role and --wake
- **WHEN** a worktree with no chat role runs `keel shift ready "next: rerun R007"`
- **THEN** it exits 1 naming `keel chat role --set` and `--wake`, and no note is stored

#### Scenario: A worktree without a chat role changes shift by hand
- **WHEN** a worktree with no chat role runs `keel shift ready --force-reason "the owner opens it" "next: rerun R007"`, a new session starts there, and it runs `keel shift resume`
- **THEN** the note is stored under `keel-chat/shift/worktree/` and records `Started by hand: the owner opens it`, `keel context` and the SessionStart projection name `keel shift resume`, `resume` prints the note and moves it to history, and afterwards `keel context` no longer names it

#### Scenario: The note comes from --file
- **WHEN** `keel shift ready --file missing.md` runs where no such file exists, and then `keel shift ready --file -` runs with the note on stdin
- **THEN** the first exits 1 with a `keel shift:` error naming `missing.md` and no stack trace, and the second stores the note given on stdin

### Requirement: The coordinator starts the new shift once its note waits

`keel shift start <role>` MUST refuse while no note waits for `<role>`, and otherwise MUST post in the direct group a message that wakes `<role>` and tells it to run `keel context` and then `keel shift resume`, followed by any next-step text given.

#### Scenario: Start before ready is refused
- **WHEN** `rtl` runs `keel shift start verify` before `verify` is ready
- **THEN** it exits non-zero and posts nothing

#### Scenario: Start wakes the role with the resume instruction
- **WHEN** `rtl` runs `keel shift start verify` after `verify` is ready
- **THEN** a message naming `keel shift resume` reaches `dm-rtl--verify` and `verify`'s signal file was touched

### Requirement: The new shift resumes from the note

While a note waits for the worktree's role, or for the worktree when it has no role, `keel context` and the SessionStart projection MUST include one line naming `keel shift resume`, without changing the context's status, selection, or next action. `keel shift resume` MUST print the note, move it to `keel-chat/shift/history/`, and, when the worktree has a role, post that the role is on shift to the coordinator of the latest shift request; after that the line MUST no longer appear; with no note waiting it MUST say so and exit 0. Run in the Claude desktop app, `resume` MUST, when it prints a note, also say to turn Remote Control back on with `set_remote_control`, because a clear there does not keep it; elsewhere it MUST NOT.

#### Scenario: The notice points to the note and resume consumes it
- **WHEN** a note waits for `verify`, the SessionStart projection runs in its worktree, and `verify` then runs `keel shift resume`
- **THEN** the projection names `keel shift resume`, the command prints the note text, the note moves to history, `dm-rtl--verify` gains an on-shift message, and the next projection no longer names it

#### Scenario: A resumed desktop shift is told to restore Remote Control
- **WHEN** a role resumes its note with `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID` set, and another resumes without them
- **THEN** the first output names `set_remote_control` and the second does not

### Requirement: Shift state is visible

`keel shift status` MUST list, for each role with a shift record or note, whether a request is open, a note waits, or the role resumed, with times.

#### Scenario: Status follows the steps
- **WHEN** `rtl` has requested a shift change of `verify`, and `verify` is ready
- **THEN** `keel shift status` lists `verify` with a waiting note

### Requirement: The coordinator starts the others before its own shift ends

`keel shift check`, run by a role that requested shift changes, MUST report each other role whose note waits, whose latest request came from it, and that it has not started since the note was written, so that its `keel shift ready` is refused until it starts them or gives `--force-reason`. `keel shift resume`, run by such a role's new shift, MUST list the roles still waiting for `keel shift start`. The request text and the `ready` output MUST name host-session state a clear destroys, such as scheduled jobs and Remote Control, as something the note should carry. Keel MUST NOT start a role on its own.

#### Scenario: A coordinator cannot leave while notes wait unstarted
- **WHEN** `rtl` requested a shift change of `verify`, `verify` ran `ready`, and `rtl` runs `keel shift check`
- **THEN** it reports `verify` as unstarted and exits 1, and `keel shift ready` by `rtl` is refused
- **AND THEN** after `rtl` runs `keel shift start verify`, `rtl`'s check no longer reports it

#### Scenario: A new coordinator learns who still waits
- **WHEN** `rtl` ran `ready --force-reason` with `verify` unstarted, and `rtl`'s new shift runs `keel shift resume`
- **THEN** the output lists `verify` as still waiting for `keel shift start`

### Requirement: A role's note is filed under the role from any worktree

`keel shift ready --role <role>` MUST file the note under `<role>` and close its open requests when `<role>` has an open shift request and the worktree is bound to no other role, and MUST be refused otherwise, naming why. `keel shift ready` without `--role`, in a worktree with no chat role while any role's shift request is open, MUST be refused, naming `--role` and those roles.

#### Scenario: A role working elsewhere files its note under the role
- **WHEN** `verify` has an open request and its session runs `keel shift ready --role verify "…"` in an unbound worktree
- **THEN** the note is `verify`'s, its request closes, and `keel shift start verify` is accepted

#### Scenario: An unbound worktree does not misfile
- **WHEN** a session in an unbound worktree runs `keel shift ready "…"` while `verify` has an open request
- **THEN** it is refused, naming `--role verify`, and no worktree note is written

### Requirement: Status suggests only what works

For a note filed under a worktree, `keel shift status` MUST say to run `keel shift resume` in that worktree, naming its path, and MUST NOT suggest `keel shift start`. For a role with an open request and no note, it MUST name any worktree note written since that request.

#### Scenario: A worktree note's hint works
- **WHEN** a worktree note waits
- **THEN** its status line names the worktree path and `keel shift resume`, and contains no `keel shift start`

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it. In the Claude desktop app, which Keel recognises by `CLAUDE_CODE_ENTRYPOINT=claude-desktop` together with a non-empty `CLAUDE_CODE_HOST_SESSION_ID`, a clear starts no session until a prompt arrives. There, `ready` MUST record the desktop session id in the note, and `ready --wake` MUST NOT say the waiter wakes the new session. Its output MUST instead name a one-shot scheduled task created before the clear with `create_scheduled_task`, whose prompt calls `send_message` to that session id with the resume instruction and asks the woken session to turn Remote Control back on first. The output MUST also name the `permissions.allow` entry `mcp__ccd_session_mgmt__set_remote_control` that step needs, and the entry `mcp__ccd_session_mgmt__clear_session`, saying that a clear left waiting for approval lets the wake arrive first and is then refused. Keel MUST NOT create the task.

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
- **THEN** the first note records `Desktop session: local_test-319`, and its output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control`, `mcp__ccd_session_mgmt__set_remote_control` and `mcp__ccd_session_mgmt__clear_session`, and does not say `The wake is armed`; the second output says `The wake is armed` and names neither `send_message` nor `create_scheduled_task`

### Requirement: A role neither starts itself nor loses its note to another worktree

`keel shift start <role>` run by `<role>` itself MUST be refused, naming `ready --wake`, and MUST create no group. `keel shift resume --role <role>` MUST read `<role>`'s note from a worktree bound to no other role, and MUST be refused in a worktree bound to another role. `keel shift status` MUST say that a role's note with no request is resumed by the role's own next session.

#### Scenario: Starting yourself is refused
- **WHEN** `pm` runs `keel shift start pm`
- **THEN** it exits non-zero naming `ready --wake`, and no group `dm-pm--pm` exists

#### Scenario: A new shift in another worktree resumes the role's note
- **WHEN** `pm` stored its note and its new session opens in an unbound worktree and runs `keel shift resume --role pm`
- **THEN** it prints `pm`'s note and moves it to history

### Requirement: A cleared shift's conversation stays findable

The chat hooks of a session bound to a role MUST record each transcript file it runs in, `keel shift history` MUST also find the Claude transcripts already kept for the role's bound worktrees, leaving out scheduled runs, with when it started and when the next replaced it, and MUST undo that record for a host-run session. `keel shift history [<role>]` MUST list the role's transcript segments and past shift notes, newest first, and with `--grep <text>` MUST print matching conversation lines per segment and exit 1 when nothing matches. `ready` MUST say the conversation stays findable, and the clear hint MUST say to turn Remote Control off before clearing.

#### Scenario: The previous shift's transcript is found after a clear
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and a scheduled run starts in transcript C in the same worktree
- **THEN** `keel shift history verify` lists B as current and A as ended, does not list C, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A
