## ADDED Requirements

### Requirement: A session changes its own shift and is woken once its next session starts

`keel shift ready --wake`, for a role bound to the worktree or named with `--role`, MUST store the note and leave a detached one-shot waiter. The waiter MUST write exactly one wake record addressed to the role, from a sender other than the role, once the role's presence shows a session started with source `clear` or `startup` at or after the `ready`, and only while the role's note still waits; it MUST then exit, and MUST give up without writing after its time limit. A SessionStart with any other source MUST NOT trigger it. `ready --wake` with no chat role MUST be refused. The chat SessionStart hook MUST record the session's start time and source in the role's presence. This is the one exception to Keel scheduling nothing, and the protocol MUST state it.

#### Scenario: The cleared session is woken once
- **WHEN** `dev` runs `keel shift ready --wake "…"`, a SessionStart with source `compact` follows, and then one with source `clear`
- **THEN** no wake record exists after the `compact` start, and after the `clear` start `dev` has one unread record from `keel-shift` naming `keel shift resume`, and `keel chat notice --check` for `dev` exits 0

#### Scenario: A role without a coordinator is told how its new session starts
- **WHEN** a role that no request named runs `keel shift ready` without `--wake`
- **THEN** the output says nobody is set to start the new session and names `--wake`

### Requirement: A role neither starts itself nor loses its note to another worktree

`keel shift start <role>` run by `<role>` itself MUST be refused, naming `ready --wake`, and MUST create no group. `keel shift resume --role <role>` MUST read `<role>`'s note from a worktree bound to no other role, and MUST be refused in a worktree bound to another role. `keel shift status` MUST say that a role's note with no request is resumed by the role's own next session.

#### Scenario: Starting yourself is refused
- **WHEN** `pm` runs `keel shift start pm`
- **THEN** it exits non-zero naming `ready --wake`, and no group `dm-pm--pm` exists

#### Scenario: A new shift in another worktree resumes the role's note
- **WHEN** `pm` stored its note and its new session opens in an unbound worktree and runs `keel shift resume --role pm`
- **THEN** it prints `pm`'s note and moves it to history
