## ADDED Requirements

### Requirement: Binding drift is reported and removed bindings can be pruned

Keel MUST report a role bound to a worktree that no longer exists, and a bound role with addressed unread records or a waiting shift note whose presence shows no activity for two hours, in `keel patrol`, `keel patrol --since-last` when it changes, and `keel --doctor`. `keel chat role --prune` MUST remove exactly the bindings to worktrees that no longer exist and name each. A session starting in a worktree with no role while other worktrees have one MUST be told which roles are unattended.

#### Scenario: Drift is reported, pruned, and named to an unbound session
- **WHEN** role `ghost` is bound to a worktree that is then removed, `verify` has a waiting shift note and no presence, and `rtl` runs `keel patrol`
- **THEN** it prints a drift line naming `ghost` and the removed worktree and one naming `verify` and its shift note, `keel --doctor` prints both as `chat roles: drift`, a session starting in an unbound worktree is told `verify` is unattended, and `keel chat role --prune` removes the `ghost` binding only
