## MODIFIED Requirements

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

### Requirement: A session changes its own shift with one slash command

The Claude plugin MUST ship `/keel:shift`, a command file at `plugins/keel/commands/shift.md` that has the session run `keel shift check`, deal with each item it reports or ask the owner, write the hand-off note, and run `keel shift ready --wake --file -` with the note on stdin through a quoted heredoc, and then do what `ready` prints for the host. It MUST say that `keel shift check` leaves out the host's own keep-awake, such as `caffeinate`, and MUST tell the session to stop a process it started or ask the owner, and to give `--force-reason` naming a process only when the owner lets it stay. The `keel shift` commands and flags it names MUST be ones `keel shift` accepts.

#### Scenario: The command's own steps hand a shift over
- **WHEN** the command file's `keel shift` lines run in order in a clean worktree bound to `verify`
- **THEN** `keel shift check` exits 0, `keel shift ready --wake --file -` stores the note given in the heredoc at `keel-chat/shift/verify.md` and prints that the wake is armed, and the command's text names `caffeinate` and `--force-reason`
