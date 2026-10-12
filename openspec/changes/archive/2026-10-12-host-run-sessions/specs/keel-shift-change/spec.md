## MODIFIED Requirements

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready` and that start has stayed unchanged for a settle time, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it.

#### Scenario: The cleared session is woken once
- **WHEN** `dev` runs `keel shift ready --wake "…"`, a SessionStart with source `compact` follows, and then one with source `clear`
- **THEN** no wake record exists after the `compact` start, and after the `clear` start `dev` has one unread record from `keel-shift` naming `keel shift resume`, and `keel chat notice --check` for `dev` exits 0

#### Scenario: A role without a coordinator is told how its new session starts
- **WHEN** a role that no request named runs `keel shift ready` without `--wake`
- **THEN** the output says nobody is set to start the new session and names `--wake`

#### Scenario: A host run's start does not wake the role
- **WHEN** `dev` runs `keel shift ready --wake "…"`, a session starts in `dev`'s worktree with source `startup`, and its first prompt starts with `<scheduled-task`
- **THEN** no wake record exists after the settle time, and a later `clear` start still wakes `dev` once
