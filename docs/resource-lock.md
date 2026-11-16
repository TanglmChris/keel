# Shared resource leases

Use a bounded lease to coordinate a checkout, branch, tool or other resource
that one session should use at a time:

    keel lock acquire main-checkout --for 2h --note "integration run"
    keel lock list
    keel lock release main-checkout

A local lease enforces nothing on Git or the filesystem. Sessions must honor it.
It is a coordination signal, not access control or a filesystem lock.

Every worktree of one clone sees the same local leases in the repository's git common directory,
under `keel-chat/locks/<resource>.json`. A lease records its holder, role (or
null), worktree, acquisition time, expiry, note and waiters. With a chat role,
the holder is that role; otherwise it is `worktree:<name>-<path hash>`.

Resource names contain 1–64 letters, digits, ".", "_" or "-", starting with a
letter or digit. Both `--for` and a non-empty `--note` are required. A duration
is a positive integer followed by s, m, h or d.

Acquiring another holder's live lease exits 1, names its holder, worktree,
expiry and note, and records you as a waiter once. Two simultaneous acquirers
of a free resource have exactly one winner. Acquiring your own lease again
replaces the expiry and note while retaining its acquisition time and waiters.
Only the holder can release; there is no force release.

Release sends each waiter with a role a direct chat message. Keel schedules
nothing: each lock command frees expired leases it notices and sends the
holder and waiters with roles one expiry message per role. The sender is the
running worktree's role, which is not messaged itself: every freed lease is
printed to the command that freed it. With no sender role, nobody is messaged
and the freed lease is only printed. With `--json`, those notices go to stderr
to keep stdout valid JSON. A lease is freed before anyone is told: a message
that cannot be posted, for example to an archived direct group, is printed to
stderr as `keel lock: warning: …` naming the role, and the command still
succeeds (#403).

`keel lock list --json` prints an object with a leases array.
`acquire --json` includes the lease and the coordination notice. All commands
support `--repo <path>`. `keel shift check` reports live leases held by its
worktree as lock loose ends, without freeing expiry or sending messages.
Release them before handing over a shift, or explain why they may remain.

Counted resources such as CPU slots are outside this exclusive lease model.
Use one resource per slot (`cpu-1` through `cpu-8`) when that is sufficient.

Lease updates briefly serialize through `keel-chat/locks/.mutation`. A command
waits up to five seconds before reporting a busy store. No command holds it
longer than a moment, so one older than 30 seconds, left by a killed process,
is removed by the next command.

## Branch locks across devices (#526)

A local lease lives in one machine's chat store, so two machines never see each
other's. A branch lock is the cross-device kind:

    keel lock acquire --branch feat [--for 45m] [--note why] [--push]
    keel lock acquire --branch feat --break "the other machine is gone"
    keel lock release --branch feat
    keel lock list

The lease is the ref `refs/keel/lock/<branch>` on the branch's remote (its
upstream remote, else `origin`). Each update is an empty-tree commit whose
message carries `keel-lock: held|released`, `Holder` (this lease holder, a role
or worktree, followed by `@<device>`), `Device`, `Seq`, `Expires`, `Head` (the
remote's sha for the branch) and `Reason`, plus `Took-over:` or `Broke:` when
taken, and its parent is the lock commit observed after fetching. The push uses
no force, so of two devices acting on the same observation git accepts exactly
one; the other is told the lock was taken. A default `git fetch` does not bring
`refs/keel/*`; Keel fetches it by an explicit refspec.

- A free branch, or one released whose `Head` the local branch contains, is
  acquired; a device whose branch does not contain the previous holder's `Head`
  or the remote branch is refused until it fetches and integrates.
- The holder acquiring again renews: a later `Expires` and a higher `Seq`.
- A lock held by another device is refused, naming holder, expiry and head, and
  the requester is recorded here as a waiter, until it is past `Expires` plus a
  5-minute grace: then it is taken over with `Took-over:` and the output shows
  the last head that holder recorded beside the remote's sha. A live lock is
  taken only with `--break "<reason>"`, recorded as `Broke:`.
- `release` requires the lock to be this device's and live, the worktree that
  has the branch checked out to be clean, and the remote branch to contain the
  local one; it then publishes `released` with that `Head` and messages the
  waiters recorded here.
- `--for` defaults to `sync: ttl:` (30 minutes), `--note` to `work on <b>`.
  `--push` first pushes the branch itself, fast-forward, where `push` or a
  matching `push:<glob>` covers it and it is not `push-protected`.

Keel pushes a lock ref only under `authorize: device-sync`; without it
`acquire` and `release --branch` exit 3. Every push runs the repository's hooks,
and a failing hook is printed once and leaves the lease to lapse. A refusal
exits 1 and a malformed request 2. A branch lock, like a local lease, cannot stop
`git push` by hand; git's own non-fast-forward refusal is the last guard.

This machine's name is a random id with the host name, written once to
`keel-chat/device.json`; `KEEL_DEVICE` names the device instead where several
share one store. `keel lock list` and `keel sync status` show each branch lock
as last fetched; `keel sync status --verify` also says when the remote's lock
has moved since.
