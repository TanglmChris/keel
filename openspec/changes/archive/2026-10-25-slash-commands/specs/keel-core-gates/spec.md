## MODIFIED Requirements

### Requirement: Semantic judgment remains agent-owned

Keel MUST NOT claim that deterministic gate structure proves product intent, behavioral test sufficiency, design quality, or risk completeness. Required semantic conclusions MUST be recorded by the current agent in task Review evidence. Wherever a durable follow-up owner is required, the accepted forms MUST include an external tracker reference alongside the repository-local forms.

#### Scenario: Completion Review is required
- **WHEN** a task is presented to `task-complete`
- **THEN** its Evidence contains Review `Status`, `Acceptance check`, `Scope check`, and `Findings`
- **AND THEN** a missing or non-passing required Review produces `needs-review`

#### Scenario: Findings require durable ownership
- **WHEN** Review identifies an unresolved finding
- **THEN** `task-complete` requires a durable OpenSpec task, new change, archive-evidence owner, absolute `http` or `https` tracker reference, or explicit discard rationale
- **AND THEN** `keel/HANDOFF.md` is not accepted as that owner

#### Scenario: An external tracker owns a finding without a local proxy file
- **WHEN** a Review `Findings` value or an `## Expectation Coverage` `Durable owner:` entry names an absolute `http` or `https` reference
- **THEN** the gate accepts it as a durable owner without requiring a repository-local file written only to satisfy the shape
- **AND THEN** both checks accept the tracker form, and every form either check accepted before is still accepted

#### Scenario: Gate does not reinterpret acceptance
- **WHEN** command Evidence and Review are present
- **THEN** Core validates their required shape and references
- **AND THEN** Core does not replace `review-checklist` by independently judging whether the command proves Acceptance

### Requirement: A finding resolved in its own task is recorded as resolved

`keel gate task-complete` MUST require a durable owner only for a finding that is still unresolved, which is what this capability and `review-checklist` already state. A finding that was found and fixed inside the task recording it MUST have an accepted form of its own, so that no author has to record a repair as a discard in order to pass the gate.

The resolved disposition MUST carry evidence. Keel MUST accept an `M<n>` check label of the same task, or a repo-relative path that exists, and MUST NOT accept the marker alone — a disposition that asserts its own conclusion is weaker than the two it joins. Keel MUST NOT accept an `http` or `https` reference as evidence of resolution, because an external tracker means the work is owned elsewhere, which is the durable-owner state.

Every form accepted before this requirement MUST still be accepted, and `keel/HANDOFF.md` MUST still be refused in all of them.

The `finding-owner` diagnostic MUST state its actionable instruction — name a path after `Durable owner:` — immediately after its opening sentence, before it enumerates the three accepted disposition forms. A reader who has forgotten to name a path is looking for what to do, and a menu of three forms read before the one instruction that applies to all of them makes the reader parse the menu to find it.

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

#### Scenario: The actionable instruction leads the diagnostic
- **WHEN** `task-complete` produces `finding-owner` for a Findings value carrying no recognized disposition
- **THEN** the sentence directing a path to be named after `Durable owner:` appears before the sentence naming the `Resolved here:` form
- **AND THEN** the three disposition forms named in the prior scenario are unchanged in content, only in position relative to the instruction

### Requirement: Two tasks shaped like one behavior are named at task-start

`keel gate task-start` MUST warn when another task in the same change declares an identical Touch set and the selected task's strategy is red-green, naming the other task so the author compares two things rather than being told something is wrong.

Keel MUST NOT fail or return `needs-review` for this shape. A genuine vertical split can share files, the judgment is semantic, and there is no mechanism to acknowledge a `needs-review` — turning a signal into a verdict would leave a legitimate split unstartable. The warning MUST NOT change the gate's status or exit code.

`review-checklist` MUST ask the same question at completion, when the evidence that settles it exists.

#### Scenario: An identical Touch set under a red-green strategy is named
- **WHEN** `task-start` selects a task whose Touch set matches another task in the same change and whose strategy is red-green
- **THEN** the result carries a warning naming the other task
- **AND THEN** the status is unchanged and the exit code is unchanged, so the task starts normally

#### Scenario: A differing Touch set or a non-red-green strategy is silent
- **WHEN** no other task in the change declares the same Touch set, or the selected task's strategy is not red-green
- **THEN** no warning about task shape is produced
