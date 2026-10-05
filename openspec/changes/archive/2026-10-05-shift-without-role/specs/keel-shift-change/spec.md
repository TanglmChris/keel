## MODIFIED Requirements

### Requirement: The outgoing shift leaves a note and closes the request

`keel shift ready` MUST run the readiness check and refuse while it reports items unless `--force-reason <text>` is given; MUST refuse an empty note; MUST store the note, taken from its text argument, `--file`, or stdin, in the repository's common directory, outside every worktree: at `keel-chat/shift/<role>.md` when the worktree has a chat role, and otherwise at `keel-chat/shift/worktree/<name>-<id>.md` for the worktree; MUST NOT require a chat role; MUST, when the worktree has a role, close the open shift request addressed to it with a reply opening `done`; and MUST print how to clear the session without clearing it.

#### Scenario: Ready is refused while loose ends remain
- **WHEN** `keel shift ready "note"` runs in a worktree the check reports items for
- **THEN** it exits non-zero, names the items, and stores no note

#### Scenario: Ready stores the note and closes the request
- **WHEN** the worktree is clean and `verify` runs `keel shift ready "next: rerun R007 on 1b64e8c"`
- **THEN** the note file holds that text, the request todo is done, and the output names `clear_session` and `/clear`

#### Scenario: A worktree without a chat role changes shift
- **WHEN** a worktree with no chat role runs `keel shift ready "next: rerun R007"`, a new session starts there, and it runs `keel shift resume`
- **THEN** the note is stored under `keel-chat/shift/worktree/`, `keel context` and the SessionStart projection name `keel shift resume`, `resume` prints the note and moves it to history, and afterwards `keel context` no longer names it


### Requirement: The new shift resumes from the note

While a note waits for the worktree's role, or for the worktree when it has no role, `keel context` and the SessionStart projection MUST include one line naming `keel shift resume`, without changing the context's status, selection, or next action. `keel shift resume` MUST print the note, move it to `keel-chat/shift/history/`, and, when the worktree has a role, post that the role is on shift to the coordinator of the latest shift request; after that the line MUST no longer appear; with no note waiting it MUST say so and exit 0.

#### Scenario: The notice points to the note and resume consumes it
- **WHEN** a note waits for `verify`, the SessionStart projection runs in its worktree, and `verify` then runs `keel shift resume`
- **THEN** the projection names `keel shift resume`, the command prints the note text, the note moves to history, `dm-rtl--verify` gains an on-shift message, and the next projection no longer names it
