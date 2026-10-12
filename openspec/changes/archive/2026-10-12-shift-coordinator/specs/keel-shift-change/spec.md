## ADDED Requirements

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
