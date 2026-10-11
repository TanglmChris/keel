## ADDED Requirements

### Requirement: The projection names the chat role a session speaks as

`keel context` MUST carry a `role` field naming the chat role bound to the current worktree, or null. When the current worktree has no role while the repository's chat binds a role to another worktree, `keel context` MUST warn, naming `keel chat role --set <name>`, and the SessionStart and compaction projection MUST carry that reminder; when a role is bound, the projection MUST name it. A repository whose chat binds no role MUST get neither the line nor the warning. Keel MUST NOT compare against the host's session title, which it cannot observe.

#### Scenario: A bound role is named
- **WHEN** the worktree is bound to `verify` and the SessionStart hook runs
- **THEN** `keel context --json` carries `role: verify` and the projection names `verify`

#### Scenario: An unbound worktree among bound ones is reminded
- **WHEN** another worktree of the repository is bound to `rtl` and this one has no role
- **THEN** `keel context` warns naming `keel chat role --set` and the projection carries the reminder

#### Scenario: A repository without chat roles is unchanged
- **WHEN** no worktree of the repository has a chat role
- **THEN** `keel context` carries `role: null` and neither warning nor projection line appears
