## MODIFIED Requirements

### Requirement: Gate execution is deterministic and write-bounded

Core gates MUST run locally without network access or model calls, except that a repository declaring `sync: lock: true` lets `task-start` and `change-close`, and only those, make one read-only `git ls-remote` for the checked-out branch and its lock ref. The only permitted project writes are the disposable `keel-write-guard/v1` manifest written by a passing `task-start` on the Claude target when `--no-guard` is absent, and the single-line replacement of the selected task's `- Contract:` Evidence anchor performed by a passing `task-start` when the caller explicitly passes `--record` and the anchor does not already hold the compiled fingerprint line. `task-complete`, `change-close`, and every failing or `needs-review` outcome MUST NOT write project state. Gates MUST return `pass`, `fail`, or `needs-review` through one versioned machine-readable result.

#### Scenario: Passing gate is process success
- **WHEN** every deterministic requirement for a gate is satisfied
- **THEN** gate status is `pass`
- **AND THEN** the command exits successfully

#### Scenario: Policy non-pass is distinguishable
- **WHEN** a gate detects a contract failure or required semantic review is absent
- **THEN** status is `fail` or `needs-review`
- **AND THEN** the process result is nonzero and distinguishable from an operational error

#### Scenario: Gate does not mutate evidence
- **WHEN** a gate evaluates task or change state
- **THEN** it does not mark tasks complete, write Review evidence, update HANDOFF, or repair artifacts
- **AND THEN** the guard manifest and the explicit `--record` Contract-anchor replacement, each written only by a passing `task-start`, are the sole exceptions to gate write-freedom

#### Scenario: Without the declaration no gate touches the network
- **WHEN** a repository declares no `sync:` and runs `task-start` and `change-close` with its remote unreachable
- **THEN** both return the verdict they return with no remote at all, and neither runs `ls-remote`


## ADDED Requirements

### Requirement: Under the lock declaration, task-start requires this device's lock and pushed work

With `sync: lock: true`, `task-start` MUST fail unless one `git ls-remote` shows the branch's lock at the sha this device last pushed, that commit is `held` by this device and unexpired by its own `Expires`, and the remote's sha for the branch equals HEAD or has HEAD as an ancestor in the local objects. It MUST NOT acquire, renew or push. `task-complete` MUST be unchanged.

#### Scenario: A task starts while the device holds the lock
- **WHEN** the lock is held by this device and unexpired and the branch is pushed
- **THEN** `task-start` passes and `ls-remote` ran once

#### Scenario: A task does not start without the lock
- **WHEN** another device took the lock, or this device's lease expired, or no lock exists
- **THEN** `task-start` fails naming the state and `keel lock acquire --branch <b>` or `keel shift resume`, and nothing was pushed

#### Scenario: A task does not start over unpushed commits
- **WHEN** the device holds the lock and the branch has a commit the remote lacks
- **THEN** `task-start` fails naming the commit and `git push origin <branch>`

#### Scenario: A stale tracking ref does not satisfy the gate
- **WHEN** `origin/feat` locally equals HEAD but the remote's `feat` is a commit the local objects do not contain
- **THEN** `task-start` fails naming both shas and `git fetch`

#### Scenario: An unreachable remote fails by name
- **WHEN** the remote cannot be reached while the lock is declared
- **THEN** `task-start` and `change-close` fail with `cannot verify` and git's error

#### Scenario: task-complete is unchanged
- **WHEN** the lock is declared and the task's own changes are uncommitted
- **THEN** `task-complete` returns what it returns without the declaration and runs no `ls-remote`

### Requirement: Under the lock declaration, change-close requires everything pushed

With `sync: lock: true`, `change-close` MUST apply the `task-start` conditions and in addition fail on any uncommitted or untracked path and unless the remote's sha for the branch equals HEAD. A repository with no remote MUST pass with a warning that nothing was checked. It MUST NOT write project state.

#### Scenario: change-close fails on an uncommitted path
- **WHEN** the lock is held, HEAD equals the remote's sha, and one path is uncommitted
- **THEN** `change-close` fails naming the path

#### Scenario: change-close passes when everything is pushed
- **WHEN** the lock is held, the tree is clean and HEAD equals the remote's sha
- **THEN** `change-close` passes the check
