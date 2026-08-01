## ADDED Requirements

### Requirement: A repository declares delegation in its own block

Keel MUST read an optional `delegation:` declaration from `keel/config.yaml` stating whether a task may be implemented by a subagent and which capability tier runs it. An absent, empty, or undeclared block MUST leave delegation unauthorized, and Keel MUST NOT extend the `authorize:` closed set to carry it.

#### Scenario: A declaring repository permits delegation
- **WHEN** `keel/config.yaml` declares a `delegation:` block naming a tier
- **THEN** Keel resolves delegation as permitted for that repository at that tier
- **AND THEN** the resolution is reported without spawning, activating, or scheduling anything

#### Scenario: No declaration preserves current behavior
- **WHEN** `keel/config.yaml` is absent, declares no `delegation:` block, or declares an empty one
- **THEN** delegation is unauthorized and every task executes in the current agent exactly as it does without this capability
- **AND THEN** no gate, evidence requirement, Review, or write-guard behavior differs in any way

#### Scenario: The standing-authorization vocabulary is not a delegation channel
- **WHEN** `authorize:` lists `delegate` or any other name outside its closed set
- **THEN** Keel reports the unrecognized entry with the accepted `authorize:` names
- **AND THEN** delegation remains unauthorized, because `authorize:` never grants it

### Requirement: A task inherits the delegation declaration only where it authored none

Keel MUST apply the repository delegation declaration as the default a task did not author. A task that authors its own delegation entry MUST keep it unchanged, and the compiled capsule MUST name `keel/config.yaml` as the source of any entry the declaration supplied.

#### Scenario: A silent task inherits the repository default
- **WHEN** a task authors no delegation entry and `keel/config.yaml` declares one
- **THEN** the compiled capsule carries the declared tier
- **AND THEN** the capsule names `keel/config.yaml` as that entry's source

#### Scenario: A task that authored its own entry keeps it
- **WHEN** a task authors a delegation entry and `keel/config.yaml` declares a different one
- **THEN** the compiled capsule carries the task's entry unchanged
- **AND THEN** the declaration does not override, merge with, or annotate it

### Requirement: Delegation requires an active write-guard manifest

Keel MUST refuse delegation when no write-guard manifest is active, and MUST decide this before a delegate starts rather than infer it from the delegate's behavior afterward.

#### Scenario: Delegation without an active manifest is refused
- **WHEN** delegation is otherwise authorized and `keel/guard.json` is absent
- **THEN** Keel refuses the delegation and names the missing manifest as the reason
- **AND THEN** it directs the caller to `keel gate task-start`

#### Scenario: The refusal is not inferable from a delegate's writes
- **WHEN** a delegate writes successfully with no manifest present
- **THEN** that success is not evidence the write was checked, because an absent manifest passes every write through silently
- **AND THEN** Keel's refusal is required to precede the delegate rather than follow its report

### Requirement: The delegation brief is write-capable and separate from the helper brief

Keel MUST compile a write-capable delegation brief as a contract distinct from `keel-helper-brief/v1`, and MUST NOT admit mutation intent into the read-only helper contract. The delegation brief MUST carry the selected task, required Read context, the Touch write boundary, the verification checks, the capsule fingerprint, the declared tier, and the prohibited actions.

#### Scenario: A delegation brief carries the write boundary
- **WHEN** an authorized delegation brief is compiled
- **THEN** it names the selected task, Read context, Touch write boundary, verification checks, fingerprint, declared tier, and prohibitions
- **AND THEN** it is not authorized to change Acceptance, mark tasks complete, sync, archive, commit, or transfer Keel ownership

#### Scenario: The read-only helper contract keeps its guarantee
- **WHEN** a mutation verb is submitted to the read-only helper brief surface
- **THEN** it is refused exactly as it is refused today
- **AND THEN** the helper contract's before/after repository byte-identity verification is unchanged

### Requirement: A delegate's return is a claim the current agent re-verifies

Keel MUST treat a delegate's reported command results as a claim rather than evidence. The current agent MUST re-run each `M<n>` verification check itself before recording Evidence, and a delegate's completion MUST NOT satisfy `task-complete`, mark the task checkbox, or settle Review.

#### Scenario: Reported results are not recorded as Evidence
- **WHEN** a delegate returns reporting that its verification checks passed
- **THEN** the current agent re-runs each `M<n>` check and records its own results as Evidence
- **AND THEN** the delegate's reported results are not recorded as Evidence

#### Scenario: Byte-identity verification is unavailable for a writer
- **WHEN** a delegate that was authorized to write returns
- **THEN** the repository byte-identity check that validates a read-only helper return does not apply, because writing is what the delegate was authorized to do
- **AND THEN** re-running the verification checks is what restores current-agent evidence

#### Scenario: A delegate cannot complete a task
- **WHEN** a delegate reports the selected task finished
- **THEN** completion still requires `keel gate task-complete`, current-agent Review, and the current agent's own checkbox write
- **AND THEN** the delegate's report settles none of them

### Requirement: Capability tiers are abstract and target-resolved

Keel MUST name capability tiers and MUST NOT name a concrete model. A tier MUST describe the capability the work requires rather than an estimate of the work's size, and the target runtime MUST resolve a tier to whatever model it provides.

#### Scenario: Keel carries a tier and resolves no model
- **WHEN** a delegation is authorized at a declared tier
- **THEN** Keel carries the tier name to the target and performs no model selection
- **AND THEN** no Keel surface names, records, or requires a concrete model identifier

#### Scenario: Keel does not observe which model ran
- **WHEN** a delegated task completes
- **THEN** Keel records the declared tier and does not claim to know which model executed the work
- **AND THEN** the surfaces state this limitation rather than implying the tier was enforced

#### Scenario: A tier is never inferred from the work
- **WHEN** no tier is declared by the task or the repository
- **THEN** Keel does not estimate one from Touch size, diff size, task count, or apparent difficulty
- **AND THEN** delegation is unauthorized, because an undeclared tier is not a tier

### Requirement: An unavailable tier refuses delegation rather than substituting one

Keel MUST refuse delegation when the current target cannot provide the declared tier, and MUST report the declared tier beside what the target offers. Keel MUST NOT silently substitute a different tier.

#### Scenario: An unprovidable tier is reported, not substituted
- **WHEN** the declared tier is not among those the current target provides
- **THEN** Keel refuses the delegation and reports the declared tier and the available ones
- **AND THEN** no work runs at a tier the owner did not declare

### Requirement: Delegation authorizes only delegation

Keel MUST keep every gate, evidence requirement, semantic Review, and write-guard behavior identical whether or not delegation is declared. A delegation declaration MUST NOT admit work, trigger execution, widen triage, or authorize any action outside routing execution.

#### Scenario: A declaring repository and a silent one gate identically
- **WHEN** the same task is completed in a repository declaring `delegation:` and in an otherwise identical repository declaring none
- **THEN** `keel gate task-start` and `keel gate task-complete` return the same status, the same problem set, and the same failure text
- **AND THEN** the write guard binds the same Touch boundary in both

#### Scenario: Delegation is not a trigger
- **WHEN** delegation is declared and a task is selected
- **THEN** `keel context` returns the same selection and next action it returns without the declaration
- **AND THEN** no delegate is spawned until the current agent decides to delegate

#### Scenario: Delegation and triage govern different questions
- **WHEN** an unattended run admitted by `triage:` reaches a task whose delegation is declared
- **THEN** the run may delegate exactly where the declaration permits it
- **AND THEN** delegation neither admits work that triage refused nor authorizes a merge
