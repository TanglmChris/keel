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

`keel shift check`, run in a worktree, MUST report as items: uncommitted changes; commits reachable from HEAD that no remote-tracking ref contains, unless the repository has no remote, which it MUST report as a note rather than an item; an active write guard; processes whose working directory is inside the worktree, other than the checking process and its ancestors; linked worktrees other than the current and main ones whose path lies under a temporary directory; and, for the worktree's chat role, open todos assigned to it other than shift requests and unread records that would wake it. It MUST exit 1 when any item is present and 0 otherwise, change nothing, and with `--json` print the items.

#### Scenario: Each kind of loose end is reported
- **WHEN** the `verify` worktree has an uncommitted file, a commit not on its remote, `keel/guard.json`, a running process started in it, a linked worktree under the temporary directory, and an open todo assigned to `verify`
- **THEN** `keel shift check` exits 1 and names each of them

#### Scenario: A clean worktree is ready
- **WHEN** those are cleared
- **THEN** `keel shift check` exits 0

### Requirement: The outgoing shift leaves a note and closes the request

`keel shift ready` MUST run the readiness check and refuse while it reports items unless `--force-reason <text>` is given; MUST refuse an empty note; MUST store the note, taken from its text argument, `--file`, or stdin, at `keel-chat/shift/<role>.md` in the repository's common directory, outside every worktree; MUST close the open shift request addressed to the role with a reply opening `done`; and MUST print how to clear the session without clearing it.

#### Scenario: Ready is refused while loose ends remain
- **WHEN** `keel shift ready "note"` runs in a worktree the check reports items for
- **THEN** it exits non-zero, names the items, and stores no note

#### Scenario: Ready stores the note and closes the request
- **WHEN** the worktree is clean and `verify` runs `keel shift ready "next: rerun R007 on 1b64e8c"`
- **THEN** the note file holds that text, the request todo is done, and the output names `clear_session` and `/clear`

### Requirement: The coordinator starts the new shift once its note waits

`keel shift start <role>` MUST refuse while no note waits for `<role>`, and otherwise MUST post in the direct group a message that wakes `<role>` and tells it to run `keel context` and then `keel shift resume`, followed by any next-step text given.

#### Scenario: Start before ready is refused
- **WHEN** `rtl` runs `keel shift start verify` before `verify` is ready
- **THEN** it exits non-zero and posts nothing

#### Scenario: Start wakes the role with the resume instruction
- **WHEN** `rtl` runs `keel shift start verify` after `verify` is ready
- **THEN** a message naming `keel shift resume` reaches `dm-rtl--verify` and `verify`'s signal file was touched

### Requirement: The new shift resumes from the note

While a note waits for a role, the role's session-start chat notice MUST include one line naming `keel shift resume`. `keel shift resume` MUST print the note, move it to `keel-chat/shift/history/`, and post that the role is on shift to the coordinator of the latest shift request, and after that the notice MUST no longer carry the line; with no note waiting it MUST say so and exit 0.

#### Scenario: The notice points to the note and resume consumes it
- **WHEN** a note waits for `verify`, its SessionStart hook runs, and `verify` then runs `keel shift resume`
- **THEN** the notice names `keel shift resume`, the command prints the note text, the note moves to history, `dm-rtl--verify` gains an on-shift message, and the next SessionStart notice no longer names it

### Requirement: Shift state is visible

`keel shift status` MUST list, for each role with a shift record or note, whether a request is open, a note waits, or the role resumed, with times.

#### Scenario: Status follows the steps
- **WHEN** `rtl` has requested a shift change of `verify`, and `verify` is ready
- **THEN** `keel shift status` lists `verify` with a waiting note
