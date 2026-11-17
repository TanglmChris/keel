## MODIFIED Requirements

### Requirement: The readiness check reports what would be lost or left running

`keel shift check`, run in a worktree, MUST report as items: uncommitted changes; commits reachable from HEAD that no remote-tracking ref contains, unless the repository has no remote, which it MUST report as a note rather than an item; an active write guard; processes whose working directory is inside the worktree, other than the checking process, its ancestors, and a `caffeinate` whose parent is one of those ancestors — the keep-awake the session's host runs under it; linked worktrees other than the current and main ones that lie in a Claude scratchpad of a session started in this worktree, `claude-<uid>/<slug>/<session>/scratchpad/` with the slug being this worktree's path with each non-alphanumeric character turned into `-`, while it MUST report any other linked worktree under a temporary directory as a note naming its path; live `keel lock` leases this worktree holds; a stash entry made on the branch this worktree has checked out, which git records in the entry's subject as `WIP on <branch>` or `On <branch>`; and, for the worktree's chat role, open todos assigned to it other than shift requests and unread records that would wake it. It MUST also report as notes naming `keel sync status` the repository's local-only branches that no worktree has checked out, other worktrees' uncommitted or unpushed work, and stash entries of other branches or with no branch in their subject, and, where `sync: lock: true` is declared and this device holds the branch's lock, a note that `keel shift ready` releases it. It MUST exit 1 when any item is present and 0 otherwise, change nothing, and with `--json` print the items.

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

#### Scenario: A stash on this branch holds the shift, other local-only work does not
- **WHEN** the worktree is otherwise clean, a stash entry was made on its branch, another on branch `other`, and a branch `scratch` has a commit, no remote counterpart and no worktree
- **THEN** `keel shift check` exits 1 naming the first stash as an item, and lists the `other` stash and `scratch` as notes naming `keel sync status`
- **AND THEN** once the first stash is dropped it exits 0 with the two notes


## ADDED Requirements

### Requirement: Ready releases the branch lock after the check passes

Where `sync: lock: true` is declared and this device holds the branch's lock, `keel shift ready` MUST, after the check passes, write the note once to `shift-notes/<role>/<UTC time>-<device>.md`, run `keel chat archive sync`, and release the lock as `keel lock release --branch` does with `Note` naming that path. It MUST refuse with exit 1 and store nothing when the release fails, and MUST say when the archive did not push, so the note stayed on this machine.

#### Scenario: Ready hands the branch over
- **WHEN** the lock is declared and held, the worktree is clean and pushed, and `keel shift ready "next: rerun R007"` runs
- **THEN** the lock is `released` with `Head` at the remote's sha and `Note` naming a `shift-notes/` path whose file holds the note

#### Scenario: A failed release stores nothing
- **WHEN** the remote cannot be reached while `keel shift ready` runs
- **THEN** it exits 1 naming the cause, stores no note, and the lock is unchanged

### Requirement: The stored note lists what is not on the remote

`keel shift ready` MUST append the check's local-only notes, and the items a `--force-reason` let stand, to the stored note under `## Not on the remote at hand-over`, with or without the lock declaration, and MUST add no section when there is nothing to list.

#### Scenario: The note lists the local-only work
- **WHEN** no `sync:` is declared and `scratch` is local-only
- **THEN** the stored note carries the section naming `scratch` and no lock was touched

#### Scenario: Nothing to list adds nothing
- **WHEN** the check has no local-only notes or items
- **THEN** the stored note is the text given

### Requirement: Resume is the takeover

Where `sync: lock: true` is declared, `keel shift resume` MUST take the worktree branch's lock, or else the released or expired lock last held by this worktree's role. It MUST refuse a dirty worktree or a live lock held elsewhere, naming it; otherwise it MUST switch the worktree to that branch fast-forwarded to the remote tip, acquire the lock, run `keel chat archive pull`, and print the note the lock's `Note` names when none is stored locally.

#### Scenario: A fresh device takes over
- **WHEN** A, as `pm`, released `feat` with a note, and a clean worktree on device B runs `keel chat role --set pm` then `keel shift resume`
- **THEN** B's worktree is on `feat` at A's `Head`, the lock is B's, A's note is printed, and no file was discarded or reset

#### Scenario: A held branch is refused
- **WHEN** another device holds `feat` live
- **THEN** `keel shift resume` exits 1 naming the holder and prints no note as current

#### Scenario: A dirty worktree is refused
- **WHEN** the worktree has an untracked file
- **THEN** `keel shift resume` exits 1 naming it and changes nothing

### Requirement: A hand-over waits while another device holds the branch

Where `sync: lock: true` is declared, a hand-over run by `keel tick` or the hand-over waiter MUST start no new session for a role whose worktree's branch lock, as last fetched, is held live by another device, and MUST record `waiting_on` naming the branch and the holder on the entry.

#### Scenario: The Mac's tick does not start a second session
- **WHEN** a hand-off for `pm` is queued on the Mac while the VPS holds `feat` live, and `keel tick` runs
- **THEN** no session is started and `keel shift status` names `feat` and the VPS holder
