## ADDED Requirements

### Requirement: A recorded commit identifier is recognized by what makes it one

Keel's project state check MUST refuse a commit identifier recorded in an active `tasks.md`, and MUST recognize it by the property that makes a token hexadecimal rather than by the length of a digit run. A run carrying no hexadecimal letter MUST NOT be reported as a contextual commit identifier, because a phone number, timestamp, order number, port, or numeric fixture is ordinary evidence prose and refusing it asks an author to reword something that was true.

Keel MUST keep refusing recorded commit, merge, and dirty state by its wording, independently of any digit run on the line, so that narrowing what counts as a hash does not narrow the rule.

#### Scenario: A decimal number in evidence prose is not an identifier
- **WHEN** an active `tasks.md` line holds a run of decimal digits beside a word such as `commit` or `提交`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line as a contextual commit identifier

#### Scenario: A recorded hexadecimal identifier is still refused
- **WHEN** an active `tasks.md` line holds a hexadecimal token of identifier length beside such a word
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: Recorded commit wording fails on its own
- **WHEN** an active `tasks.md` records commit, merge, or dirty state in words and carries no hash-shaped token
- **THEN** `keel --check` still refuses it
