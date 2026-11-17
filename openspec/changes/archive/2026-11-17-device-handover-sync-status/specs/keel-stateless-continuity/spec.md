## ADDED Requirements

### Requirement: Context warns when work exists only on this machine

`keel context` MUST add one warning, read from local refs without touching the network, when the repository holds a local-only branch, a worktree with uncommitted or unpushed work, or a stash, as `keel sync status` defines them. It MUST give the count of each kind and name `keel sync status`, MUST add nothing when there is none or when the repository has no remote, and MUST change neither `status`, the selection nor `nextAction`. The existing uncommitted-paths warning is unchanged.

#### Scenario: A stash and a local-only branch are warned about
- **WHEN** the repository has one stash entry and one branch with no remote counterpart, and `keel context` runs
- **THEN** a warning counts one local-only branch and one stash and names `keel sync status`, and the JSON `status` and `nextAction` equal those of the same repository without them

#### Scenario: A clean repository or one with no remote adds nothing
- **WHEN** nothing is local-only, or the repository has no remote
- **THEN** `keel context` prints no sync warning

### Requirement: Context sends the session to the lock before a task

Where `sync: lock: true` is declared and `keel context` would report `task-start` or `task-complete` next while the branch's last fetched lock is not held live by this device, it MUST report `nextAction` `shift-resume` with `keel shift resume` when the lock is released or expired by this worktree's role, else `lock-acquire` with `keel lock acquire --branch <b>`, naming the holder in the reasons. It MUST keep `status` and the selection.

#### Scenario: A branch held elsewhere sends the session to acquire
- **WHEN** context would be `ready` with `task-start`, and the fetched lock of the branch is held live by another device
- **THEN** `nextAction.kind` is `lock-acquire` with `keel lock acquire --branch feat`, the reasons name the holder, and `status` and the selection are unchanged

#### Scenario: A released lock of this role sends the session to resume
- **WHEN** the lock was released by this worktree's role on another device
- **THEN** `nextAction.kind` is `shift-resume` with `keel shift resume`

#### Scenario: A device that holds the lock is not redirected
- **WHEN** this device holds a live lock
- **THEN** `nextAction` is what it is without the declaration
