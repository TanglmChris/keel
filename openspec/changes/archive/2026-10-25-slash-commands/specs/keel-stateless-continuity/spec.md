## MODIFIED Requirements

### Requirement: A task field refuses a state claim and not its provenance

Inside a task field of an active `tasks.md` — the region from a two-space `- Name:` label up to the next non-blank line indented less than two spaces — the project-state check MUST refuse a hash-shaped token only where a state claim binds it. That means a context word naming the token directly (`commit a1b2c3d`, `HEAD is at a1b2c3d`, `已提交 a1b2c3d`), or the token followed by `committed`, `merged`, or `pushed`. A token that a context word elsewhere on the line does not bind MUST pass, because a field cites the base a comparison ran against, the commit a result ran on, and the inputs a hash identifies, and `review-checklist` asks a Scope check to name that base.

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
