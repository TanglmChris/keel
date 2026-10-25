## ADDED Requirements

### Requirement: A session whose directory is gone is explained, not resumed

When the directory a role's recorded CLI session ran in — the `cwd` that `claude agents` lists for it, or else the worktree its presence records — no longer exists, `keel chat wake now <role>` MUST NOT resume it, MUST exit nonzero, and MUST say that the directory no longer exists and print a command that continues the conversation in the role's worktree with `claude --bg --fork-session --resume <id>`. Keel MUST NOT run that command itself. `keel tick` MUST NOT try such a session again for the same record. `keel patrol` MUST report each role it covers whose ended CLI session's recorded worktree no longer exists as a risk naming `keel chat wake now <role>`, and `keel shift status` MUST list those roles.

#### Scenario: A session from a renamed workspace prints the fork command
- **WHEN** verify's recorded CLI session has exited, and both `claude agents` and its presence record it in a directory that no longer exists
- **THEN** `keel chat wake now verify` runs no `claude --bg`, exits nonzero, names that directory, and prints `cd <verify's worktree> && claude --bg --fork-session --resume <its id>`
- **AND THEN** `keel tick` with a new record addressed to verify runs no `claude --bg` either, `keel patrol` reports verify as a risk naming `keel chat wake now verify`, and `keel shift status` lists verify
