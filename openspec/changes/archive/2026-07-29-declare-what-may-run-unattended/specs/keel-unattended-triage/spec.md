## ADDED Requirements

### Requirement: A repository declares which work may start without asking

Keel MUST read an optional `triage:` declaration from `keel/config.yaml` naming the issue labels
that admit an issue into the pipeline without asking the owner. An absent, empty, or undeclared
block MUST admit nothing.

#### Scenario: A declared label admits an issue
- **WHEN** `keel/config.yaml` declares `triage:` accepting the label `auto` and an issue carrying
  that label is evaluated
- **THEN** Keel reports the issue admitted
- **AND THEN** the reason names the label that admitted it

#### Scenario: No declaration admits nothing
- **WHEN** `keel/config.yaml` declares no `triage:` block, or declares an empty one
- **THEN** every issue is refused
- **AND THEN** the refusal states that the repository has declared no triage policy, rather than
  implying the issue was judged unsuitable

#### Scenario: A refusal names the policy it failed
- **WHEN** an issue carrying no accepted label is evaluated against a declared policy
- **THEN** the refusal names the labels the issue carried and the labels the declaration accepts
- **AND THEN** the reader can tell an unlabelled issue from an undeclared policy

### Requirement: Triage evaluation performs no network access

Keel MUST evaluate a triage policy against issue attributes supplied to it, and MUST NOT fetch an
issue, contact a forge, or perform any network access. The evaluation MUST be local, deterministic,
and repeatable from the same inputs.

#### Scenario: Attributes are supplied, not fetched
- **WHEN** `keel triage` is invoked with an issue's labels
- **THEN** Keel evaluates the declared policy against exactly those labels
- **AND THEN** no network call is made, and the command succeeds with no reachable network

#### Scenario: The same inputs give the same answer
- **WHEN** the same declaration and the same issue attributes are evaluated twice
- **THEN** both runs return the same verdict and the same reason

### Requirement: Admission starts work and decides nothing that follows

An admitted issue MUST enter authoring and implementation under every existing gate. Keel MUST NOT
treat admission as authority over acceptance, scope, design, evidence, review, or any material
decision reached later.

#### Scenario: Later gates are unaffected by admission
- **WHEN** an issue is admitted and work on it begins
- **THEN** expectation alignment, `task-start`, `task-complete`, `change-close`, and the write guard
  behave exactly as they do for work that was never triaged
- **AND THEN** a material decision encountered during that work still stops for the owner

#### Scenario: Stopping at a material decision is the expected outcome
- **WHEN** an unattended run reaches a decision the owner must make
- **THEN** the run stops and reports where it stopped and why
- **AND THEN** the stop is reported as the designed boundary rather than as a failure

### Requirement: An unattended run may open a pull request and may not merge

Keel MUST state that an unattended run may triage, author, implement, verify, and open a pull
request, and MUST NOT merge one. Merging MUST remain a human act regardless of any declaration.

#### Scenario: The boundary is stated where a run can read it
- **WHEN** the unattended-run protocol is inspected
- **THEN** it states that opening a pull request is permitted and merging is not
- **AND THEN** no configuration key grants a merge

#### Scenario: Standing authorization does not imply merge
- **WHEN** a repository standing-authorizes `push` and declares a triage policy
- **THEN** an unattended run may push and open a pull request
- **AND THEN** it still may not merge, because no declaration in Keel authorizes one

### Requirement: Keel ships no scheduler

Keel MUST NOT provide, imply, or claim a scheduling capability. Documentation and command output
MUST attribute the loop to the host runtime rather than to Keel.

#### Scenario: Scheduling is attributed to the host
- **WHEN** the unattended-run documentation is inspected
- **THEN** it states that scheduling is a host capability such as `/loop` or cron
- **AND THEN** no Keel command starts, stops, or registers a recurring run
