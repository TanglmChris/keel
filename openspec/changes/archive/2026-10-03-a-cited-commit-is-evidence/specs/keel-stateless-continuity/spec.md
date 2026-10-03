## ADDED Requirements

### Requirement: A task field refuses a state claim and not its provenance

Inside a task field of an active `tasks.md` — the region from a two-space `- Name:` label up to the next non-blank line indented less than two spaces — the project-state check MUST refuse a hash-shaped token only where a state claim binds it. That means a context word naming the token directly (`commit a1b2c3d`, `HEAD is at a1b2c3d`, `已提交 a1b2c3d`), or the token followed by `committed`, `merged`, or `pushed`. A token that a context word elsewhere on the line does not bind MUST pass, because a field cites the base a comparison ran against, the commit a result ran on, and the inputs a hash identifies, and `keel-review-checklist` asks a Scope check to name that base.

Inside a task field, the check MUST refuse `dirty` and `uncommitted` only as a claim about the work's state: predicative after a copula (`is still uncommitted`, `was dirty`), or as the value of a `Status` or `State` label. An attributive use (`no dirty groups`, `pre-existing dirty paths`) and a negated one MUST pass, because the word names the design under test or another checkout as often as this repository's worktree. `not committed` and `pending commit` MUST stay refused.

Lines outside every task field MUST keep the line-wide rules, and the commit-hash wording, merge, and submission rules MUST be unchanged everywhere.

#### Scenario: A cited base in a Review field is evidence
- **WHEN** a task's Evidence `Scope check` names the base it compared against and an `Acceptance check` names the commit a result ran on, on lines that also carry `hashes` or `HEAD` elsewhere
- **THEN** `keel --check` reports `keel state: ok`

#### Scenario: A base named in an Acceptance criterion is a condition
- **WHEN** a task's Acceptance criterion bounds its scope relative to a named base and says to check `HEAD` before commit
- **THEN** `keel --check` reports `keel state: ok`

#### Scenario: A domain term or a negation is not dirty state
- **WHEN** a task field says a verifier saw `no dirty groups`, or that no edits were copied `from uncommitted` changes of another checkout
- **THEN** `keel --check` reports `keel state: ok`

#### Scenario: A bound state claim in a field is still refused
- **WHEN** a task field records `committed to main as a1b2c3d`, `HEAD is at a1b2c3d`, `已合入 a1b2c3d`, `the work is still uncommitted`, or `Status: dirty`
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: A line outside any task field keeps the line-wide rule
- **WHEN** a task title line or a notes section carries a context word and a hash-shaped token apart, or the word `dirty`
- **THEN** `keel --check` reports `keel state: failed` and names the line

## MODIFIED Requirements

### Requirement: A recorded commit identifier is recognized by what makes it one

Keel's project state check MUST refuse a commit identifier recorded in an active `tasks.md`, and MUST recognize it by the property that makes a token hexadecimal rather than by the length of a digit run. A run carrying no hexadecimal letter MUST NOT be reported as a contextual commit identifier, because a phone number, timestamp, order number, port, or numeric fixture is ordinary evidence prose and refusing it asks an author to reword something that was true.

Keel MUST keep refusing recorded commit, merge, and dirty state by its wording, independently of any digit run on the line, so that narrowing what counts as a hash does not narrow the rule. This holds for every line an author writes as a statement, and what makes a line a statement is bounded by three other requirements rather than left to be inferred: a `Covers` field is a citation of a name that exists elsewhere, a quoted span is material the author cites, and inside a task field only a bound state claim is read for a hash or dirty state. None of the cited material is a record of state.

#### Scenario: A decimal number in evidence prose is not an identifier
- **WHEN** an active `tasks.md` line holds a run of decimal digits beside a word such as `commit` or `提交`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line as a contextual commit identifier

#### Scenario: A recorded hexadecimal identifier is still refused
- **WHEN** an active `tasks.md` line holds a hexadecimal token of identifier length beside such a word
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: Recorded commit wording fails on its own
- **WHEN** an active `tasks.md` records commit, merge, or dirty state in words, outside any quoted span, and carries no hash-shaped token
- **THEN** `keel --check` still refuses it

### Requirement: A Covers citation is not a record of what it cites
A `Covers` field in an active `tasks.md` MUST be exempt from the rules that read prose for recorded commit, merge, and dirty state, and from the contextual commit-hash rule. A Covers entry is a citation whose segments must resolve to a requirement or scenario that exists in a spec, or to a design reference in the change's own design; naming a requirement about dirty state is not recording dirty state, and refusing it leaves an author no repair except renaming the requirement.

The exempt region MUST be the whole `Covers` field as the task contract compiler bounds it — the label line and every line under it up to the next field label — and not the label line alone, because every citation is written on a line below the label.

Every line outside a `Covers` field MUST still be read by both rules, within the bound that the task-field requirement sets, so that exempting a citation does not exempt the evidence around it.

#### Scenario: A citation naming a requirement about dirty state is accepted
- **WHEN** an active `tasks.md` cites a published requirement whose name contains `dirty`, `uncommitted`, or `commit hash`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names any line of that `Covers` field

#### Scenario: The exemption is the field and not the label
- **WHEN** the citations sit on the lines below a `- Covers:` label rather than on the label line
- **THEN** those lines are exempt

#### Scenario: Prose outside the Covers field is still refused
- **WHEN** an `Evidence` or `Verify` line of the same task states that the worktree was dirty
- **THEN** `keel --check` reports `keel state: failed` and names that line
