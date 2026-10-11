## ADDED Requirements

### Requirement: A session leases a shared resource with an expiry and a note

`keel lock acquire <resource> --for <duration> --note <text>` MUST record a lease in the repository's chat store, shared by every worktree, naming the holder (the worktree's chat role, or the worktree when it has none), the worktree, the acquisition time, the expiry, and the note. It MUST refuse a missing `--for` or `--note`, a duration not of the form `<n>s|m|h|d`, and a resource name outside 1–64 letters, digits, `.`, `_`, and `-` starting with a letter or digit. It MUST state that the lease enforces nothing on Git or the filesystem. `keel lock list` MUST print every live lease with its holder, worktree, expiry, and note, and `--json` MUST print them as data.

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

Only the holder MUST be able to release a lease; a release by anyone else MUST be refused, naming the holder. Release MUST post a direct chat message naming the resource to each waiter that has a chat role. Keel schedules nothing, so every `keel lock` command MUST first free each expired lease it finds and, when the running worktree has a chat role, post once to the holder and each waiter with a role that the lease expired; without a role it MUST print the freed lease instead.

#### Scenario: Release by the holder tells the waiters
- **WHEN** `sweep` waits on `main-checkout`, `sweep` tries `keel lock release main-checkout`, and then `integ` runs it
- **THEN** the first exits 1 naming `integ`, and the second exits 0
- **AND THEN** `sweep` has a direct message naming `main-checkout` released, and the lease is gone from `keel lock list`

#### Scenario: An expired lease is freed by the next command
- **WHEN** `integ` holds `main-checkout` with `sweep` waiting, the lease's expiry passes, and `sweep` runs `keel lock list`
- **THEN** the lease is gone, `integ` has a direct message naming `main-checkout` expired, and `sweep` can then acquire it
