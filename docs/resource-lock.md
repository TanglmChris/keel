# Shared resource leases

Use a bounded lease to coordinate a checkout, branch, tool or other resource
that one session should use at a time:

    keel lock acquire main-checkout --for 2h --note "integration run"
    keel lock list
    keel lock release main-checkout

A lease enforces nothing on Git or the filesystem. Sessions must honor it.
It is a coordination signal, not access control or a filesystem lock.

Every worktree sees the same leases in the repository's git common directory,
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
to keep stdout valid JSON.

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
