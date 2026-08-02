## ADDED Requirements

### Requirement: A finding resolved in its own task is recorded as resolved

`keel gate task-complete` MUST require a durable owner only for a finding that is still unresolved, which is what this capability and `keel-review-checklist` already state. A finding that was found and fixed inside the task recording it MUST have an accepted form of its own, so that no author has to record a repair as a discard in order to pass the gate.

The resolved disposition MUST carry evidence. Keel MUST accept an `M<n>` check label of the same task, or a repo-relative path that exists, and MUST NOT accept the marker alone — a disposition that asserts its own conclusion is weaker than the two it joins. Keel MUST NOT accept an `http` or `https` reference as evidence of resolution, because an external tracker means the work is owned elsewhere, which is the durable-owner state.

Every form accepted before this requirement MUST still be accepted, and `keel/HANDOFF.md` MUST still be refused in all of them.

#### Scenario: A finding fixed in the task passes without a discard reason
- **WHEN** Review `Findings` records a finding as resolved in this task and names an `M<n>` check of the same task as the evidence
- **THEN** `task-complete` accepts it without requiring a durable owner or a discard reason
- **AND THEN** the same text with no evidence named is refused

#### Scenario: Resolution evidence may be a path that exists
- **WHEN** a resolved finding names a repo-relative path as its evidence
- **THEN** the gate accepts it when that path exists and refuses it by name when it does not
- **AND THEN** an `http` or `https` reference is refused as resolution evidence while remaining accepted as a durable owner

#### Scenario: The accepted-forms diagnostic names all three dispositions
- **WHEN** `task-complete` produces `finding-owner` for a Findings value carrying no recognized disposition
- **THEN** the message names the resolved-here form and its evidence requirement alongside the durable-owner and discard forms
- **AND THEN** it still directs a path to be named after `Durable owner:` so it reads as the owner rather than a file the finding mentions
