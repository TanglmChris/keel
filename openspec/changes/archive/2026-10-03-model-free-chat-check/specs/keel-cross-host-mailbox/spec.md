## ADDED Requirements

### Requirement: A model-free check tells a scheduler whether to start a turn

`keel chat notice --check` MUST print nothing, MUST NOT advance any cursor or write any record, and MUST exit 0 when the bound role has an unread record that would wake it — a mention by name or alias, a todo assigned to it, or a message in its direct group — and exit 1 otherwise, including outside a repository and with no role bound.

#### Scenario: A mention makes the check pass
- **WHEN** `verify` has one unread `@verify` record and runs `keel chat notice --check`
- **THEN** it exits 0 with no output
- **AND THEN** `keel chat unread --json` still reports that record

#### Scenario: A broadcast alone does not start a turn
- **WHEN** `verify`'s only unread record is an `@all` message
- **THEN** `keel chat notice --check` exits 1 with no output

#### Scenario: Nowhere to answer is not an error
- **WHEN** `keel chat notice --check` runs outside any git repository, or in a worktree with no role
- **THEN** it exits 1 with no output
