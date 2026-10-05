## MODIFIED Requirements

### Requirement: The readiness check reports what would be lost or left running

`keel shift check`, run in a worktree, MUST report as items: uncommitted changes; commits reachable from HEAD that no remote-tracking ref contains, unless the repository has no remote, which it MUST report as a note rather than an item; an active write guard; processes whose working directory is inside the worktree, other than the checking process and its ancestors; linked worktrees other than the current and main ones that lie in a Claude scratchpad of a session started in this worktree, `claude-<uid>/<slug>/<session>/scratchpad/` with the slug being this worktree's path with each non-alphanumeric character turned into `-`, while it MUST report any other linked worktree under a temporary directory as a note naming its path; and, for the worktree's chat role, open todos assigned to it other than shift requests and unread records that would wake it. It MUST exit 1 when any item is present and 0 otherwise, change nothing, and with `--json` print the items.

#### Scenario: Each kind of loose end is reported
- **WHEN** the `verify` worktree has an uncommitted file, a commit not on its remote, `keel/guard.json`, a running process started in it, a linked worktree in a scratchpad of a session started in `verify`, and an open todo assigned to `verify`
- **THEN** `keel shift check` exits 1 and names each of them

#### Scenario: A clean worktree is ready
- **WHEN** those are cleared
- **THEN** `keel shift check` exits 0

#### Scenario: Another session's temporary worktree does not block
- **WHEN** a linked worktree lies in the scratchpad of a session started in another directory, and nothing else is loose
- **THEN** `keel shift check` exits 0 and lists that worktree as a note
