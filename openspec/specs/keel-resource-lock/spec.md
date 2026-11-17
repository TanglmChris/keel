# keel-resource-lock Specification

## Purpose

Leases on shared resources between sessions: exclusive, bounded, explained, visible to every worktree, and ended by release or noticed expiry with the waiters told. A lease is a coordination signal and enforces nothing.

## Requirements

### Requirement: A session leases a shared resource with an expiry and a note

`keel lock acquire <resource> --for <duration> --note <text>` MUST record a lease in the repository's chat store, shared by every worktree, naming the holder (the worktree's chat role, or the worktree when it has none), the worktree, the acquisition time, the expiry, and the note. Without `--branch`, it MUST refuse a missing `--for` or `--note`, a duration not of the form `<n>s|m|h|d`, and a resource name outside 1–64 letters, digits, `.`, `_`, and `-` starting with a letter or digit. It MUST state that the lease enforces nothing on Git or the filesystem. `keel lock list` MUST print every live lease, and every branch lock as last fetched, with its holder, worktree, expiry, and note, and `--json` MUST print them as data.

#### Scenario: A lease is acquired and listed
- **WHEN** worktree `a` with role `integ` runs `keel lock acquire main-checkout --for 2h --note "integration run"`
- **THEN** it exits 0 and says the lease enforces nothing
- **AND THEN** `keel lock list` in worktree `b` names `main-checkout`, `integ`, its expiry, and the note

#### Scenario: A claim without a bound or a reason is refused
- **WHEN** `keel lock acquire main-checkout --note x` runs without `--for`, or with `--for 5x`, or without `--note`, or for the resource `../x`
- **THEN** each exits non-zero naming what is missing or malformed, and no lease is recorded

### Requirement: A lease is exclusive, and a refused requester waits

`keel lock acquire` MUST refuse a resource another holder's live lease holds, exiting 1 and naming that holder, its worktree, its expiry, and its note, and MUST record the requester as a waiter once. Of two acquirers racing for a free resource, exactly one MUST succeed. The holder acquiring its own lease MUST renew it with the new expiry and note.

#### Scenario: A held resource is refused and the requester waits
- **WHEN** `integ` holds `main-checkout` and worktree `b` with role `sweep` runs `keel lock acquire main-checkout --for 1h --note "formal sweep"`
- **THEN** it exits 1 naming `integ`, its expiry, and "integration run"
- **AND THEN** `keel lock list --json` shows `sweep` among the waiters, once even after a second refused attempt

#### Scenario: The holder renews
- **WHEN** `integ` acquires `main-checkout` again with `--for 3h --note "integration, extended"`
- **THEN** it exits 0 and the lease carries the later expiry and the new note

### Requirement: A lease ends at release or at its noticed expiry, and waiters are told

Only the holder MUST be able to release a lease; a release by anyone else MUST be refused, naming the holder. Release MUST post a direct chat message naming the resource to each waiter that has a chat role. Keel schedules nothing, so every `keel lock` command MUST first free each expired lease it finds and, when the running worktree has a chat role, post once to the holder and each waiter with a role that the lease expired; without a role it MUST print the freed lease instead. A lease MUST be freed before anyone is told, and a message that cannot be posted MUST be printed as a warning naming the role and MUST NOT fail the command or keep the lease.

#### Scenario: Release by the holder tells the waiters
- **WHEN** `sweep` waits on `main-checkout`, `sweep` tries `keel lock release main-checkout`, and then `integ` runs it
- **THEN** the first exits 1 naming `integ`, and the second exits 0
- **AND THEN** `sweep` has a direct message naming `main-checkout` released, and the lease is gone from `keel lock list`

#### Scenario: An expired lease is freed by the next command
- **WHEN** `integ` holds `main-checkout` with `sweep` waiting, the lease's expiry passes, and `sweep` runs `keel lock list`
- **THEN** the lease is gone, `integ` has a direct message naming `main-checkout` expired, and `sweep` can then acquire it

#### Scenario: A notice that cannot be posted does not keep the lease
- **WHEN** `integ` holds `main-checkout`, `sweep` waits, their direct group is archived so no message can be posted to it, and `integ` runs `keel lock release main-checkout`
- **THEN** it exits 0, the lease is gone from `keel lock list`, and stderr carries a warning naming `sweep`

#### Scenario: Long role names are told on release
- **WHEN** `kaiwu-design-iecc` holds `cpu-heavy`, `kaiwu-pm-iecc` waits, and `kaiwu-design-iecc` runs `keel lock release cpu-heavy`
- **THEN** it exits 0 with no warning, `keel lock list` exits 0 without the lease, and `dm-kaiwu-design-iecc--kaiwu-pm-iecc` holds the release message

### Requirement: A branch lock is a lease kept as a remote ref and updated only by fast-forward

`keel lock acquire --branch <b>` MUST keep the lease as the ref `refs/keel/lock/<b>` on the branch's remote: a commit carrying `keel-lock` (`held`/`released`), `Holder` (`keel lock`'s holder plus `@<device>`), `Device`, `Seq`, `Expires` and `Head`, whose parent is the lock commit observed after fetching that ref. It MUST push without force, so of two devices acting on one observed lock exactly one succeeds. `--for` MUST default to the TTL and `--note` to `work on <b>`.

#### Scenario: Two devices race for a free branch
- **WHEN** devices A and B, with the same bare remote and no lock for `feat`, both run `keel lock acquire --branch feat` at once
- **THEN** exactly one exits 0 and the other exits 1 saying the lock was taken, and the remote's `refs/keel/lock/feat` holds one `held` commit with `Seq: 1`

#### Scenario: The record names its holder
- **WHEN** role `pm` on device `mac-1a2b3c4d` acquires `feat`
- **THEN** the lock commit's `Holder` is `pm@mac-1a2b3c4d`, `Head` is the remote's sha for `feat`, and `Expires` is the TTL after the push

### Requirement: A branch lock is exclusive across devices and renewed by its holder

`keel lock acquire --branch` MUST refuse, exiting 1 and pushing no lock commit, when the lock is `held` by another device and not past its `Expires` plus 5 minutes, naming the holder, the expiry and the `Head`, and MUST record the requester as a waiter the way a local lease does. The holder acquiring again MUST renew with a later expiry and a higher `Seq`.

#### Scenario: A second device is refused and waits
- **WHEN** A holds `feat` and B, as role `verify`, runs `keel lock acquire --branch feat`
- **THEN** B exits 1 naming `pm@mac-1a2b3c4d`, the expiry and the head, the remote lock is unchanged, and `verify` is listed as a waiter

#### Scenario: The holder renews
- **WHEN** A runs it again
- **THEN** it exits 0 and the lock carries `Seq: 2` and a later `Expires`

### Requirement: A branch lock is acquired only where the previous holder finished

`keel lock acquire --branch` MUST refuse, exiting 1 and pushing nothing, while the local branch does not contain the lock's `Head` or the remote branch's tip after fetching, saying to fetch and integrate first.

#### Scenario: A device that is behind is refused
- **WHEN** A released `feat` with `Head` C3 and B's local `feat` is at C1
- **THEN** B's acquisition exits 1 naming C3, and the lock stays `released`

#### Scenario: A device at the head acquires
- **WHEN** B fast-forwards `feat` to C3 and acquires
- **THEN** it exits 0 and the lock is `held` by B with `Seq` one higher

### Requirement: An expired branch lock is taken over with a warning, and a live one only by breaking it

When the lock is `held` by another device and past its `Expires` plus 5 minutes, acquisition MUST take it, record `Took-over` naming the previous holder, and print the last `Head` that holder recorded beside the remote branch's sha. A live lock MUST be taken only by `--break "<reason>"`, which records `Broke` with the reason, and `--break` without a reason MUST exit 2. Neither MUST use a force push.

#### Scenario: An expired lock is taken and the gap is shown
- **WHEN** A stopped renewing 40 minutes ago with `Head` C2 while the remote `feat` is at C4, and B's `feat` is at C4
- **THEN** B's acquisition exits 0 with `Took-over: pm@mac-1a2b3c4d`, and the output shows C2 and C4

#### Scenario: A live lock needs an explicit break
- **WHEN** A's lock is live and B runs `keel lock acquire --branch feat --break "A's machine is gone"`
- **THEN** it exits 0, the lock carries `Broke: pm@mac-1a2b3c4d — A's machine is gone`, and the remote ref advanced by fast-forward

### Requirement: Releasing a branch lock confirms the push

`keel lock release --branch <b>` MUST, for the holder of a live lock, require a clean worktree and one `git ls-remote` showing the remote branch at HEAD or a descendant of it locally, then push a `released` commit with that sha as `Head` and, when a note was handed over, its archived path as `Note`. Otherwise, or for another device's lock, it MUST exit 1 and push nothing. It MUST message the waiters as a local release does.

#### Scenario: Release after a verified push
- **WHEN** the holder's `feat` is clean and pushed, and it releases
- **THEN** it exits 0, the remote lock is `released` with `Head` equal to the remote's `feat`, and each waiter has a message naming `feat`

#### Scenario: Release refuses unpushed work or another device's lock
- **WHEN** `feat` has a commit the remote lacks, or B releases a lock A holds
- **THEN** it exits 1 naming the commit and `git push origin feat`, or naming A, and the lock is unchanged

### Requirement: Keel pushes a lock ref only under `device-sync`, and a work branch only under `push`

Every Keel command that pushes a lock ref MUST refuse with exit 3 naming `device-sync` when `authorize:` does not declare it, and push nothing. Keel MUST push a work branch only where `push` or a matching `push:<glob>` covers it and it is not `push-protected`, MUST NOT force, create a tag or delete a ref, and MUST run the repository's push hooks, reporting a failing hook once.

#### Scenario: Undeclared authorization pushes nothing
- **WHEN** `authorize:` lacks `device-sync` and `keel lock acquire --branch feat` runs
- **THEN** it exits 3 naming `device-sync` and the remote is unchanged

#### Scenario: A branch outside `push:` is not pushed
- **WHEN** `device-sync` and `push:claude/*` are declared and the tick renews the lock of `feat`, which has an unpushed commit
- **THEN** the lock is renewed, `feat` on the remote is unchanged, and the output names `push:claude/*`

### Requirement: A repository may require the branch lock at its sync points

Keel MUST read an optional `sync:` declaration from `keel/config.yaml` with the keys `lock` (a boolean, default false) and `ttl` (`<n>m` or `<n>h`, 5 minutes to 24 hours, default 30 minutes). Anything else MUST be named by `keel context` and `keel --doctor` and MUST behave as absent. Without `lock: true` no gate, guard, check, hook, hand-over or next action MUST behave differently from before.

#### Scenario: A valid declaration is read
- **WHEN** `sync:` declares `lock: true` and `ttl: 45m`
- **THEN** the lock is in force and leases last 45 minutes

#### Scenario: An unreadable declaration is named and ignored
- **WHEN** `sync:` declares `ttl: soon` or an unknown key
- **THEN** `keel context` and `keel --doctor` name it and nothing behaves differently from a repository with no declaration

### Requirement: The holder's leases are renewed by the tick and the prompt hook

Where `device-sync` is declared, each `keel tick` MUST renew every branch lock this device holds whose worktree exists and then push the branch as `push` allows; the prompt-time hook MUST renew only when more than a third of the TTL has passed since the last renewal, at most once per interval, and MUST stay silent when it fails. Neither MUST acquire, break or release a lock, and a failure MUST leave the lease to lapse.

#### Scenario: The tick renews from the filesystem root
- **WHEN** this device holds `feat`'s lock, `push` is declared, `feat` has a committed unpushed commit, and a tick started from `/` runs
- **THEN** the remote lock has a later `Expires`, its `Head` is the remote's `feat`, and the remote `feat` includes the commit

#### Scenario: The hook renews once per interval and fails quietly
- **WHEN** two prompts arrive within one interval, then the remote is unreachable at the next due prompt
- **THEN** only the first renews, and the due prompt prints nothing and does not fail

### Requirement: Lock events reach the roles through the chat

Acquisition, release, take-over and break of a branch lock MUST each post one record to the new holder's and the previous holder's roles where each has one, so that the events travel wherever the chat archive or Slack bridge carries the chat.

#### Scenario: A take-over is announced
- **WHEN** B takes over A's expired lock
- **THEN** A's role has a record naming `feat`, B, and the last head A recorded

### Requirement: Doctor reports the branch locks of this device

`keel --doctor` MUST print a `sync` line naming the `sync:` declaration, this device's id, each branch lock this device holds with its expiry and last renewal, and whether the tick or the prompt hook renews here.

#### Scenario: A held lock is reported
- **WHEN** this device holds `feat`'s lock
- **THEN** the `sync` line names `feat`, its expiry and its last renewal
