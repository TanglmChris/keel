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

`keel shift check`, run in a worktree, MUST report as items: uncommitted changes; commits reachable from HEAD that no remote-tracking ref contains, unless the repository has no remote, which it MUST report as a note rather than an item; an active write guard; processes whose working directory is inside the worktree, other than the checking process, its ancestors, and a `caffeinate` whose parent is one of those ancestors — the keep-awake the session's host runs under it; linked worktrees other than the current and main ones that lie in a Claude scratchpad of a session started in this worktree, `claude-<uid>/<slug>/<session>/scratchpad/` with the slug being this worktree's path with each non-alphanumeric character turned into `-`, while it MUST report any other linked worktree under a temporary directory as a note naming its path; live `keel lock` leases this worktree holds; and, for the worktree's chat role, open todos assigned to it other than shift requests and unread records that would wake it. It MUST exit 1 when any item is present and 0 otherwise, change nothing, and with `--json` print the items.

#### Scenario: Each kind of loose end is reported
- **WHEN** the `verify` worktree has an uncommitted file, a commit not on its remote, `keel/guard.json`, a running process started in it, a linked worktree in a scratchpad of a session started in `verify`, a live `keel lock` lease, and an open todo assigned to `verify`
- **THEN** `keel shift check` exits 1 and names each of them

#### Scenario: A clean worktree is ready
- **WHEN** those are cleared
- **THEN** `keel shift check` exits 0

#### Scenario: Another session's temporary worktree does not block
- **WHEN** a linked worktree lies in the scratchpad of a session started in another directory, and nothing else is loose
- **THEN** `keel shift check` exits 0 and lists that worktree as a note

#### Scenario: The host's keep-awake is not a loose end
- **WHEN** the worktree is otherwise clean and holds a `caffeinate` whose parent is an ancestor of the checking process, an orphaned `caffeinate`, and a `sleep`, all started in it
- **THEN** `keel shift check` names the orphaned `caffeinate` and the `sleep` and not the first
- **AND THEN** with only the first left running it exits 0

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

`keel shift start <role>` MUST refuse while no note waits for `<role>`, and otherwise MUST post in the direct group a message that wakes `<role>` and tells it to run `keel context` and then `keel shift resume`, followed by any next-step text given. When the waiting note records `Desktop session: <id>`, the output MUST NOT say the role was woken: a session with no running process on the Claude desktop app sees no chat record (#320). It MUST instead name `get_session`, `unarchive_session`, `send_message`, the session id, and the start text, as the step that wakes it.

#### Scenario: Start before ready is refused
- **WHEN** `rtl` runs `keel shift start verify` before `verify` is ready
- **THEN** it exits non-zero and posts nothing

#### Scenario: Start wakes the role with the resume instruction
- **WHEN** `rtl` runs `keel shift start verify` after `verify` is ready
- **THEN** a message naming `keel shift resume` reaches `dm-rtl--verify` and `verify`'s signal file was touched

#### Scenario: Start for a desktop note names the wake step
- **WHEN** `verify`'s note was written on the Claude desktop app as session `local_test-320` and `rtl` runs `keel shift start verify`
- **THEN** the start record still reaches `dm-rtl--verify`, and the output names `send_message`, `get_session`, `unarchive_session`, `local_test-320`, and `keel shift resume`, and does not say `Woke`

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

### Requirement: Shift state is visible

`keel shift status` MUST list, for each role with a shift record or note, whether a request is open, a note waits, or the role resumed, with times. A waiting note that records a `Desktop session:` and was written longer ago than the overdue time — 3 minutes, which `KEEL_SHIFT_WAKE_OVERDUE_MS` overrides — MUST be listed as an overdue desktop wake naming that session id, `list_task_runs`, and `send_message`; a younger one, or one recording no desktop session, MUST NOT.

#### Scenario: Status follows the steps
- **WHEN** `rtl` has requested a shift change of `verify`, and `verify` is ready
- **THEN** `keel shift status` lists `verify` with a waiting note

#### Scenario: An overdue desktop wake is flagged
- **WHEN** `verify` runs `keel shift ready --wake` in the desktop app with session `local_test-319`, and `keel shift status` runs once with the overdue time far away and once with it passed
- **THEN** the first output does not say `overdue`, and the second says `overdue` and names `local_test-319`, `list_task_runs` and `send_message`

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

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it. In the Claude desktop app, which Keel recognises by `CLAUDE_CODE_ENTRYPOINT=claude-desktop` together with a non-empty `CLAUDE_CODE_HOST_SESSION_ID`, a clear starts no session until a prompt arrives. There, `ready` MUST record the desktop session id in the note and the process id of the nearest ancestor process whose command's basename is `claude` (`KEEL_SHIFT_DESKTOP_PID` overrides it) as `Desktop process: <pid>.`, and `ready --wake` MUST NOT say the waiter wakes the new session. Its output MUST instead give these steps in this order, and MUST NOT tell the session to turn Remote Control off: create, or update when it exists, an ad-hoc scheduled task named `keel-shift-wake-<role>` with neither `fireAt` nor `cronExpression`, whose prompt first runs `keel shift await-clear --pid <pid>` with Bash and, when that exits 1, sends nothing, calls `PushNotification`, and starts its reply with `WAKE FAILED`, and when it exits 0 calls `get_session` on that session id and, when it reports the session archived, calls `unarchive_session` on it, then calls `send_message` to it with the resume instruction, which asks the woken session to restore Remote Control and its title as `keel shift resume` says, and, if that send is still refused because the session is archived, unarchives it and sends once more, saying which path it took, and treats a send result of `delivered` or `queued` as a delivered wake and any other result, after that retry, as a failed wake, for which it calls `PushNotification` naming the session and the result and starts its reply with `WAKE FAILED`; the output MUST say that the app's auto-archive can archive the cleared session before the wake and that unarchiving brings back its worktree, MUST NOT tell the session to dismiss its bound PRs, MUST say that the run waits for the clear itself, so starting it before the clear is safe, MUST NOT schedule the wake for a later time, and MUST say that Remote Control stays on across the clear and the app reconnects it under a new address that a remote viewer has to open; start that task at once with `run_scheduled_task`; rename the outgoing session with `set_session_title` so it reads as between shifts until the woken session renames it back, without calling it an archived copy; and call `clear_session("self")`. When `authorize:` declares `self-shift`, the output MUST say the repository standing-authorizes these four steps, so the session takes them without asking; otherwise it MUST name `self-shift` as the declaration that would. The output MUST name the `permissions.allow` entries `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session`, `mcp__ccd_session_mgmt__unarchive_session` and `mcp__scheduled-tasks__run_scheduled_task` and the `authorize:` entry `shift-restore` that an unattended restore needs, and MUST NOT give approval of `clear_session` as a reason. Keel MUST NOT create the task. `keel shift await-clear --pid <pid>` MUST exit 0 once that process no longer exists and MUST exit 1 when it still exists after its time limit (120 s by default, `--timeout-ms` overrides).

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
- **THEN** the first note records `Desktop session: local_test-319`, and its output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control`, `set_session_title`, `mcp__ccd_session_mgmt__set_remote_control` and `shift-restore`, does not name `set_remote_control("self", false)`, names `create_scheduled_task` before `set_session_title` and `set_session_title` before `clear_session`, names `get_session` before `unarchive_session` and `unarchive_session` before `send_message`, names `delivered`, `PushNotification` and `WAKE FAILED`, names `await-clear`, `run_scheduled_task` and `keel-shift-wake-dev`, names `run_scheduled_task` before `set_session_title`, does not name `fireAt` nor `three minutes`, the note records `Desktop process:`, names `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session`, and neither says `The wake is armed`, `archived copy` nor names `unbind_pr`, `get_status` or `mcp__ccd_session_mgmt__clear_session`; the second output says `The wake is armed` and names none of `send_message`, `create_scheduled_task`, `unbind_pr` and `unarchive_session`

#### Scenario: A declared self-shift lets the session take its outgoing steps without asking
- **WHEN** `dev` runs `keel shift ready --wake "…"` in the desktop app, once with `authorize:` declaring `self-shift` and once without
- **THEN** the first output says `Standing-authorized by \`self-shift\``, and the second names `self-shift` as the declaration that would, without that sentence

#### Scenario: await-clear returns once the outgoing process has exited
- **WHEN** `keel shift await-clear --pid <p>` runs for a process that exits after one second, and again for a live process with `--timeout-ms 500`
- **THEN** the first exits 0 within a few seconds and says `cleared`, and the second exits 1 and says `not cleared`

### Requirement: A role neither starts itself nor loses its note to another worktree

`keel shift start <role>` run by `<role>` itself MUST be refused, naming `ready --wake`, and MUST create no group. `keel shift resume --role <role>` MUST read `<role>`'s note from a worktree bound to no other role, and MUST be refused in a worktree bound to another role. `keel shift status` MUST say that a role's note with no request is resumed by the role's own next session.

#### Scenario: Starting yourself is refused
- **WHEN** `pm` runs `keel shift start pm`
- **THEN** it exits non-zero naming `ready --wake`, and no group `dm-pm--pm` exists

#### Scenario: A new shift in another worktree resumes the role's note
- **WHEN** `pm` stored its note and its new session opens in an unbound worktree and runs `keel shift resume --role pm`
- **THEN** it prints `pm`'s note and moves it to history

### Requirement: A cleared shift's conversation stays findable

The chat hooks of a session bound to a role MUST record each transcript file it runs in, `keel shift history` MUST also find the Claude transcripts already kept for the role's bound worktrees, leaving out scheduled runs, with when it started and when the next replaced it, and MUST undo that record for a host-run session. `keel shift history [<role>]` MUST list the role's transcript segments and past shift notes, newest first, and with `--grep <text>` MUST print matching conversation lines per segment, from Claude transcripts and Codex rollouts alike, and exit 1 when nothing matches. When a role's session starts a new transcript, the hook MUST copy each ended segment's transcript that exists and has no up-to-date copy into Keel's store as gzip-compressed bytes under `shift/transcripts/<role>/`, which the chat archive does not sync, and MUST NOT copy the current segment; it MUST likewise copy each transcript `history` finds for the role that no record names and that has no copy at least as new as it, leaving out scheduled runs. When a segment's own file is gone, `history` MUST read Keel's copy, whether or not a record names it, mark the segment `(kept)` rather than `(missing)`, and `--grep` MUST search the copy. `ready` MUST say the conversation stays findable, and the clear hint MUST say to turn Remote Control off before clearing.

#### Scenario: The previous shift's transcript is found after a clear
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and a scheduled run starts in transcript C in the same worktree
- **THEN** `keel shift history verify` lists B as current and A as ended, does not list C, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A

#### Scenario: A shift's conversation outlives the host's file
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and A is then deleted
- **THEN** Keel's store holds a gzip copy of A under `shift/transcripts/verify/` and none of B, `keel shift history verify` lists A as `(kept)`, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A

#### Scenario: A Codex rollout is searched
- **WHEN** a role's segment is a Codex rollout file whose user message contains a phrase
- **THEN** `keel shift history <role> --grep <that phrase>` prints it under that segment

#### Scenario: A found transcript is kept and read after its file is gone
- **WHEN** `verify`'s bound worktree holds a transcript O that no record names and a scheduled run P, and its session then runs in transcript A and is cleared into transcript B
- **THEN** Keel's store holds a gzip copy of O under `shift/transcripts/verify/` and none of P or B, and after O is deleted `keel shift history verify` lists O as `(kept)` and `keel shift history verify --grep <a phrase said in O>` prints that phrase

### Requirement: A past shift is shown in full

`keel shift history <role> --show <session id>` MUST print the whole conversation of the role's transcript segment whose file name starts with that id or its 8-character prefix: a header naming the transcript and its time span, then each user and assistant record in file order with its timestamp and speaker and its full text, a tool call with its name and input, and a tool result with its text. It MUST read the host's transcript when it exists and Keel's kept copy otherwise, and MUST exit 1 naming the candidates when no segment or more than one matches.

#### Scenario: A removed session's shift is shown from the kept copy
- **WHEN** a segment of `verify` with a user prompt, an assistant reply, a tool call and its result has a kept copy in Keel's store, and its host transcript is then deleted
- **THEN** `keel shift history verify --show <its 8-character id>` prints the header and all four in order, each in full, from the kept copy

#### Scenario: An id that matches no segment
- **WHEN** `keel shift history verify --show 00000000` names no segment of verify
- **THEN** it exits 1 and says no segment matches

### Requirement: A resumed note's commits are checked against the remote

`keel shift resume` MUST, after printing a note, list each commit id and `<branch> @ <sha>` the note names — a commit id being 7 to 40 hex digits after `@`, or elsewhere holding at least one letter and one digit or resolving to a commit — and mark each against the remote-tracking refs as `already in origin/<default>`, `branch moved: now <sha>`, `branch gone`, or `not found`. It MUST NOT fetch, and MUST say it did not and when the refs were last fetched. A note that names no commit MUST print no list.

#### Scenario: A stale note's commits are marked
- **WHEN** a note names a commit already on `origin/<default>`, `feat @ <old>` after `feat` moved to `<new>`, `gone-branch @ <sha>` for a branch the remote lacks, `deadbee1`, and the date `20261018`, and the role runs `keel shift resume`
- **THEN** the output marks them `already in origin/<default>`, `branch moved: now <new>`, `branch gone` and `not found`, lists nothing for the date, and says the refs were not fetched

#### Scenario: An all-digit sha is still a commit
- **WHEN** a note names `digits-branch @ <sha>` and the bare `<sha>`, where the sha's first eight characters are all digits and `digits-branch` points at it
- **THEN** the pair is marked current and the bare sha is listed

### Requirement: A CLI session changes its own shift and the next one is named for its start

In a Claude Code CLI session, `keel shift ready --wake` MUST record the session id and process in the note, queue the hand-off in the chat store, arm no clear waiter, leave a detached hand-over waiter that carries the hand-over out every few seconds until the entry is no longer pending or two hours pass, and say that the session should end its turn. `keel tick` MUST carry out any queued hand-off as well, and the two MUST NOT start two sessions for one entry. A hand-over MUST leave the entry while `claude agents` shows the old session's status as anything but idle — busy, or waiting for input such as a session blocked on a question — and MUST NOT read its job state, which labels the last message rather than whether the turn has ended; once its status is idle, or it is stopped or gone it MUST retire the old session by stopping it with `claude stop`, keeping its conversation, and MUST NOT resume it, because a session running with Remote Control takes its claude.ai title back over a rename, and only then start a new session with `claude --bg -n "<role> · <MM-DD HH:MM>" --permission-mode <mode>`, named for its local start time, and a prompt to run `keel shift resume`, in the role's worktree, recording `delivered` with the new session id and name or `failed` with the reason, and starting at most one new session per entry. After a delivered hand-over it MUST keep the newest `shift: keep_old_sessions:` (default 0, so the session just handed over is removed too) stopped background sessions of the role — whose working directory is one of the role's bound worktrees, or whose transcript Keel's store keeps under the role whatever its working directory — other than the new session, counting only a session with a conversation — a transcript in the host's files or in Keel's store — and remove each older one with `claude rm` only once Keel's store holds a copy of its transcript, recording the removed ids on the entry; a session whose transcript cannot be copied MUST stay, and a session with no transcript anywhere, never given a prompt, MUST NOT be counted and MUST stay. `keel shift status` MUST list each hand-off with its state and the command that reopens the old session, and the patrol MUST report a failed hand-off, or one pending over 15 minutes, as a risk.

#### Scenario: The waker hands a CLI shift over once the old session is idle
- **WHEN** `verify`'s CLI session `5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea` (job id `5b14fbae`) runs `keel shift ready --wake`, and `claude agents --json --all` shows it busy, then waiting for input with state `blocked`, then idle with state `working`, with no `keel tick` run
- **THEN** the note records the session id and a waiter was started with no `CLAUDE*` variable in its environment; nothing is stopped or started while it is busy or waiting; once it is idle, though its state still reads `working`, the calls are, in order, `stop 5b14fbae` and `--bg -n "verify · <MM-DD HH:MM>" --permission-mode auto` with a `keel shift resume` prompt in verify's worktree, and the old session is never resumed; status shows it delivered with the new session, its name, and how to read the old one

#### Scenario: Only the newest old sessions stay listed
- **WHEN** `keel/config.yaml` declares `shift: keep_old_sessions: 2`, and after a hand-over `claude agents` lists six stopped background sessions in verify's worktree — one newer than all but the session just handed over with no transcript anywhere, and the oldest with only Keel's copy of its transcript — a stopped session in another worktree, and the new session
- **THEN** the two newest old sessions with a transcript stay; each older one is removed with `claude rm` after Keel's store holds its copy, the one with only Keel's copy included; the one with no transcript is not counted and stays, as do the other worktree's session and the new session; and `keel shift status` names the removed sessions

#### Scenario: By default the old shift leaves the session list
- **WHEN** nothing declares `shift: keep_old_sessions:`, and after a hand-over `claude agents` lists the session just handed over and three older stopped sessions of verify's, each with a transcript
- **THEN** all four are removed with `claude rm`, each only after Keel's store holds its transcript, so the role's only listed session is the new one; `keel shift history verify --show <id>` still prints each removed shift, and `keel shift status` names that command for the old session

#### Scenario: An old session from before a worktree moved is still the role's
- **WHEN** after a hand-over `claude agents` also lists a stopped session of verify's whose working directory no longer exists, whose transcript Keel's store keeps under `verify`, and a stopped session in a missing directory whose transcript Keel keeps under no role
- **THEN** the first is removed with `claude rm` and the second stays

#### Scenario: The tick and the waiter start one session
- **WHEN** a hand-over lock younger than two minutes exists for `verify` and `keel tick` runs, and then the lock is removed and `keel tick` runs twice
- **THEN** the first tick starts nothing; the second starts one session and the third none

#### Scenario: A failed hand-off is a risk
- **WHEN** the new session cannot start
- **THEN** status shows the hand-off failed with the reason, and `keel patrol` reports it as a risk

### Requirement: A session changes its own shift with one slash command

The Claude plugin MUST ship `/keel:shift`, a command file at `plugins/keel/commands/shift.md` that has the session run `keel shift check`, deal with each item it reports or ask the owner, write the hand-off note, and run `keel shift ready --wake --file -` with the note on stdin through a quoted heredoc, and then do what `ready` prints for the host. It MUST say that `keel shift check` leaves out the host's own keep-awake, such as `caffeinate`, and MUST tell the session to stop a process it started or ask the owner, and to give `--force-reason` naming a process only when the owner lets it stay. The `keel shift` commands and flags it names MUST be ones `keel shift` accepts.

#### Scenario: The command's own steps hand a shift over
- **WHEN** the command file's `keel shift` lines run in order in a clean worktree bound to `verify`
- **THEN** `keel shift check` exits 0, `keel shift ready --wake --file -` stores the note given in the heredoc at `keel-chat/shift/verify.md` and prints that the wake is armed, and the command's text names `caffeinate` and `--force-reason`

### Requirement: The CLI hand-over and wake keep to the measured host contract
A hand-over MUST NOT `claude rm` a session whose recorded process is still running; it waits for that process to exit, bounded, and keeps the session listed when it does not. When `claude agents --json --all` cannot be read or `claude` is missing, the pending hand-off MUST record why, and `keel shift status` and the patrol risk MUST name it. A tick MUST mark an ended role woken only when the resume succeeded, retry a failed resume at most three times, and not retry a removed session. A runner MUST claim a pending entry as `starting`, with its process and time, before any host call, and MUST NOT act on an entry another runner claimed; a `starting` entry whose runner is gone, or older than ten minutes, and every retry MUST first adopt a listed session named `<role> · …` in the role's worktree started since the claim, and start nothing when one exists. A tick MUST retry a failed hand-off at most three start attempts per entry, only while the old session is not running again, and never an entry that records no attempts; after the last attempt `keel shift status` and the patrol risk MUST name `keel chat wake now <role>`.

#### Scenario: The old session is removed only after its process exits
- **WHEN** a hand-over stops the old session, whose process exits a moment after `claude stop` returns
- **THEN** `claude rm` of that session runs only after the process has exited
- **AND THEN** when the process is still running past the wait, the session is not removed and stays listed

#### Scenario: A host that cannot be listed is named
- **WHEN** `claude` is missing, or `claude agents --json --all` prints no list, while a hand-off is pending
- **THEN** the hand-off stays pending and `keel shift status` names that cause

#### Scenario: A failed wake is retried a bounded number of times
- **WHEN** a role's CLI session has ended, a record addressed to it waits, and resuming it fails
- **THEN** the next tick tries again, up to three attempts for that record, and a session `claude agents` no longer lists is not tried again

#### Scenario: Concurrent runners start one session
- **WHEN** two `keel tick` runs and a hand-over waiter carry out the same pending hand-off at the same moment, and the new session takes a second to start
- **THEN** `claude --bg` runs once and the entry is delivered

#### Scenario: A runner that died while starting is settled without a second start
- **WHEN** the runner that claimed a hand-off is killed after `claude --bg` listed the new session but before it recorded the result, and `keel tick` runs
- **THEN** the entry is delivered with that listed session, marked adopted, and `claude --bg` has run once

#### Scenario: A failed hand-off is retried within a bound
- **WHEN** the new session fails to start on every attempt and `keel tick` runs five times
- **THEN** `claude --bg` has run three times, the entry stays failed, and `keel shift status` names `keel chat wake now verify`
- **AND THEN** when the start fails twice and then succeeds, the entry is delivered after the third attempt

#### Scenario: A resumed old session or an older entry is not retried
- **WHEN** a failed hand-off's old session runs again, or a failed entry records no attempts, and `keel tick` runs
- **THEN** no new session is started and the entry stays failed

### Requirement: The shift check reminds the session to recheck memory
`keel shift check` MUST print a note that tells the session to recheck what it wrote to memory before it writes the hand-off note. The note MUST appear in the text output and in the `--json` `notes`. It MUST NOT count as an item or change readiness. `/keel:shift` MUST tell the session to act on that note.

#### Scenario: A clean worktree is ready and is reminded about memory
- **WHEN** `keel shift check` runs in a clean worktree bound to a role
- **THEN** it exits 0 as ready, and both its text and its `--json` `notes` carry the memory note

### Requirement: A shift note's session ids are not read as commits

When `keel shift resume` lists the commits a note names, a bare token that is the first segment of a UUID, or that begins a session id Keel records under `sessions/` or keeps under `shift/transcripts/`, MUST NOT be listed; every other token MUST be read as before. The note header `keel shift ready` writes MUST NOT carry a blank line for a session field it leaves empty.

#### Scenario: Session ids in a note are not listed as commits
- **WHEN** a CLI session runs `keel shift ready` with a note naming a landed commit, `deadbee1`, and the first eight digits of another recorded session's id, and `keel shift resume` runs
- **THEN** the landed commit is marked `already in origin/<default>` and `deadbee1` `not found`, neither session id is listed, and the note's header holds no two consecutive blank lines

### Requirement: Resume says when the worktree is on a branch already merged

After printing a note, `keel shift resume` MUST print one line when the worktree's HEAD differs from `origin/<default>` and is an ancestor of it, naming the branch (or a detached HEAD), that it is already in `origin/<default>`, how many commits behind it is, and to start new work from `origin/<default>`. It MUST NOT fetch, and MUST print no such line when HEAD has commits `origin/<default>` lacks or no remote default branch resolves.

#### Scenario: A merged branch is named, an unmerged one is not
- **WHEN** verify's worktree is on `feat`, whose commit was pushed and fast-forwarded into the remote default branch with one more commit after it, and verify runs `keel shift ready` then `keel shift resume`
- **THEN** the resume output names `feat`, `already in origin/<default>`, and `1 commit behind`
- **AND THEN** after a new unpushed commit on `feat`, another ready and resume print no such line

### Requirement: Resuming a CLI shift removes its old sessions

When `keel shift resume` prints a note that names a `CLI session`, in a worktree with a role and in a process run by a Claude Code host, it MUST remove the role's old sessions exactly as a delivered hand-over does, under the same `shift: keep_old_sessions:`, with the note's session as the one handed over, the note's process as the one to wait for, and the current session as the new one. It MUST NOT ask the host when the role's hand-off entry is `delivered` to the current session, because that hand-over already removed them. When it removed any, it MUST name their ids and `keel shift history <role> --show <id>`, and it MUST still print the note and exit 0 when the host does not answer. A takeover that Keel did not carry out, such as a session the owner opened by hand, thereby leaves no old session listed.

#### Scenario: A hand-opened session's resume removes the old shift
- **WHEN** verify's CLI session writes a note with `keel shift ready`, its process has exited, `claude agents` lists that session stopped with a transcript, an older stopped session of verify's whose working directory no longer exists and whose transcript Keel keeps under `verify`, and a stopped session of rtl's, and a new CLI session in verify's worktree runs `keel shift resume` with nothing declared
- **THEN** the note is printed, `claude rm` removes the first two, each only after Keel's store holds its transcript, rtl's session and the current session stay, and the output names both ids and `keel shift history verify --show`

#### Scenario: Resume asks the host only when it may remove something
- **WHEN** the same note is resumed outside a Claude Code host, and again in the session that Keel's delivered hand-over started
- **THEN** neither resume calls `claude`, and both still print the note
