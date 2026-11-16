# keel-sync-status Specification

## Purpose

Make work held only on this machine visible from one read-only command and verify pushed work against the remote when requested.

## Requirements

### Requirement: One command lists what exists only on this machine

`keel sync status` MUST list, from any worktree, every worktree, local branch and stash entry of the repository that is not on the remote. A branch is local-only when no remote-tracking ref contains its tip. A worktree is, when it has uncommitted or untracked paths, a local-only branch or a detached head no remote-tracking ref contains. A stash entry always is. A worktree whose directory is missing MUST be listed as missing.

#### Scenario: Each kind of local-only work is listed
- **WHEN** a repository has `feat` two commits ahead of `origin/feat` in worktree `a`, a branch `scratch` with a commit, no remote counterpart and no worktree, worktree `b` on a pushed branch with one untracked file, a branch `done` merged into `origin/main`, and one stash entry
- **THEN** `keel sync status --json` lists `feat` (2 unpushed commits), `scratch`, worktree `b` (1 uncommitted path) and the stash entry, and does not list `done`
- **AND THEN** the command exits 1 and no ref, file or chat record changed

#### Scenario: A clean repository exits 0
- **WHEN** every worktree is clean, every branch tip is in a remote-tracking ref, and there is no stash
- **THEN** `keel sync status` says nothing is only on this machine and exits 0

### Requirement: The listing is read-only and its exit code says whether anything is local-only

`keel sync status` MUST NOT fetch, MUST NOT write to the repository or the chat store, with `--json` MUST print the same data, and MUST say that it reads the remote-tracking refs as of the last fetch, with that time. It MUST exit 0 when nothing is local-only and nothing is unverified, `remote-ahead` counting as neither, 1 when anything is, and 2 for an operational error such as running outside a repository or an unknown argument.

#### Scenario: Outside a repository is an operational error
- **WHEN** `keel sync status` runs where there is no repository, or with an unknown argument
- **THEN** it exits 2 naming the problem and lists nothing

#### Scenario: A run from the filesystem root gives the same report
- **WHEN** it runs with working directory `/` and `--repo <worktree>`
- **THEN** it prints the same report as when run inside the worktree

### Requirement: The listing shows each local branch's lock

`keel sync status` MUST show, for each local branch, the lock it last fetched — holder, state, expiry and head — or that none exists, and with `--verify` the lock as `git ls-remote` shows it, marking one whose sha differs from the last fetched.

#### Scenario: A held lock is shown
- **WHEN** `feat`'s fetched lock is held by `pm@mac-1a2b3c4d` until a stated time
- **THEN** the report shows that holder, state and expiry beside `feat`

### Requirement: `--verify` compares the remote's real sha

`keel sync status --verify` MUST run one `git ls-remote --heads` per remote involved — a branch's upstream remote, else `origin`, or the one `--remote <name>` names — limited in time and never prompting, and MUST write no ref. Without `--verify` the command MUST NOT touch the network.

#### Scenario: Without --verify the network is untouched
- **WHEN** `keel sync status` runs with a remote that cannot be reached
- **THEN** it completes from local refs with the same output as before

#### Scenario: One lookup serves every branch
- **WHEN** three local branches track the same remote and `--verify` runs
- **THEN** exactly one `ls-remote` is made and each branch is classified

### Requirement: `--verify` classifies each local branch against the remote's sha

For each local branch `--verify` MUST report `same`, `remote-behind` (the remote's sha is an ancestor of the local tip), `remote-ahead` (the tip is an ancestor of it), `diverged`, `unknown-to-local` (the remote's sha is not in the local object store) or `not-on-remote`.

#### Scenario: A stale remote-tracking ref is caught
- **WHEN** `origin/feat` locally equals the tip of `feat`, but the remote's `feat` has moved to a commit the local objects do not contain
- **THEN** `feat` is reported `unknown-to-local`, not `same`, and the command exits 1

#### Scenario: A push that landed only part of the commits is caught
- **WHEN** `feat` is three commits past the remote's `feat` and the remote-tracking ref was advanced by hand to the tip
- **THEN** without `--verify` the branch looks pushed, and with `--verify` it is reported `remote-behind` and the command exits 1

### Requirement: A failed lookup is never reported as pushed

When a `--verify` lookup fails, `keel sync status` MUST report `cannot verify` with git's error for each affected branch, MUST count those branches as unverified, and MUST NOT report any of them as `same`.

#### Scenario: A failed lookup is not a pass
- **WHEN** the remote cannot be reached while `--verify` runs
- **THEN** each affected branch is reported `cannot verify` with git's error, none is reported `same`, and the command exits 1

### Requirement: The report names the fix

For each local-only item `keel sync status` MUST print the command that puts it on the remote — `git push [-u] <remote> <branch>`, committing first for uncommitted work, `keel lock acquire --branch` or `keel lock release --branch` for a lock — and MUST NOT run any of them.

#### Scenario: The fix is printed and not run
- **WHEN** `scratch` is local-only
- **THEN** the report prints `git push -u origin scratch` and the remote has no `scratch` afterwards

### Requirement: The report says which authorization covers the fix

For each fix `keel sync status` MUST say which `authorize:` entry covers it — `commit`, `push` or a matching `push:<glob>` for a session's own commit and push, `device-sync` for what Keel pushes itself — and, when none does, MUST name the entry to declare.

#### Scenario: A push covered by a glob is said to be covered
- **WHEN** `authorize:` declares `push:feat*` and `feat` is local-only
- **THEN** the report prints `git push origin feat` and says `push:feat*` authorizes it

#### Scenario: An uncovered push names the entry to declare
- **WHEN** `authorize:` declares nothing and `scratch` is local-only
- **THEN** the report prints `git push -u origin scratch` and names `push` or `push:scratch`, and the branch is not pushed
