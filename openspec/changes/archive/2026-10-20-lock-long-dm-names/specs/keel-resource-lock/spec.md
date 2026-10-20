## MODIFIED Requirements

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
