## MODIFIED Requirements

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
