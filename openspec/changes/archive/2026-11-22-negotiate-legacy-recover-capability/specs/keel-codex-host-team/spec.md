## ADDED Requirements

### Requirement: Legacy managed recovery negotiates workspace roots support

Keel MUST negotiate the native capability required by a recovery request that restores runtime workspace roots, including legacy managed entries without a saved reviewer or effective policy snapshot. Existing writer, original identity, worktree, policy and delivery-claim checks MUST remain in force.

#### Scenario: Legacy recovery restores a drifted original thread

- **WHEN** an idle legacy role's original thread has a different native cwd
- **THEN** explicit recover negotiates the required capability and restores the recorded cwd and runtime workspace roots on the original endpoint without rewriting the registry or starting a turn
