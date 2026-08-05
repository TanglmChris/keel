## ADDED Requirements

### Requirement: A context word is a word and not a substring
The project-state check MUST treat the ASCII context words that make a hash-shaped token a recorded commit identifier — `commit`, `master`, `main`, `HEAD`, `hash` — as whole words. A word that merely contains one of them, such as `remaining`, `heading`, `domain`, or `maintains`, MUST NOT supply the context, because a word inside another word is not that word and refusing the line asks an author to reword something that was true.

The inflected forms an author actually writes MUST keep supplying the context: `commits`, `committed`, `committing`, and `hashes` name the act the rule exists to catch.

The Chinese context words MUST keep matching wherever they appear, because a word boundary is not defined between two characters that are both word characters, and requiring one would stop `已提交` and `未提交` from matching at all.

#### Scenario: A word that merely contains a context word supplies no context
- **WHEN** an active `tasks.md` line carries a hexadecimal token beside a word such as `remaining` or `heading`, and no context word of its own
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line as a contextual commit hash

#### Scenario: An inflected context word still supplies it
- **WHEN** an active `tasks.md` line carries a hexadecimal token of identifier length beside `committed`, `commits`, or `hashes`
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: A Chinese context word needs no boundary
- **WHEN** an active `tasks.md` line records commit state as `已提交` or `未提交`
- **THEN** `keel --check` still refuses it, whether or not a hash-shaped token shares the line

### Requirement: A Covers citation is not a record of what it cites
A `Covers` field in an active `tasks.md` MUST be exempt from the rules that read prose for recorded commit, merge, and dirty state, and from the contextual commit-hash rule. A Covers entry is a citation whose segments must resolve to a requirement or scenario that exists in a spec, or to a design reference in the change's own design; naming a requirement about dirty state is not recording dirty state, and refusing it leaves an author no repair except renaming the requirement.

The exempt region MUST be the whole `Covers` field as the task contract compiler bounds it — the label line and every line under it up to the next field label — and not the label line alone, because every citation is written on a line below the label.

Every line outside a `Covers` field MUST still be read by both rules, so that exempting a citation does not exempt the evidence around it.

#### Scenario: A citation naming a requirement about dirty state is accepted
- **WHEN** an active `tasks.md` cites a published requirement whose name contains `dirty`, `uncommitted`, or `commit hash`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names any line of that `Covers` field

#### Scenario: The exemption is the field and not the label
- **WHEN** the citations sit on the lines below a `- Covers:` label rather than on the label line
- **THEN** those lines are exempt

#### Scenario: Prose outside the Covers field is still refused
- **WHEN** the same wording that is exempt inside a `Covers` field appears in an `Evidence` or `Verify` line of the same task
- **THEN** `keel --check` reports `keel state: failed` and names that line

## MODIFIED Requirements

### Requirement: A recorded commit identifier is recognized by what makes it one

Keel's project state check MUST refuse a commit identifier recorded in an active `tasks.md`, and MUST recognize it by the property that makes a token hexadecimal rather than by the length of a digit run. A run carrying no hexadecimal letter MUST NOT be reported as a contextual commit identifier, because a phone number, timestamp, order number, port, or numeric fixture is ordinary evidence prose and refusing it asks an author to reword something that was true.

Keel MUST keep refusing recorded commit, merge, and dirty state by its wording, independently of any digit run on the line, so that narrowing what counts as a hash does not narrow the rule. This holds for every line an author writes as a statement. It does not extend to a `Covers` field, whose content is a citation of a name that exists elsewhere rather than a record of state, and which is exempt from both rules.

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
