## Purpose

Define how a repository declares which work may start without asking, how that declaration is evaluated without network access, what an unattended run may and may not do, and why admission is a declaration rather than an inference.
## Requirements

### Requirement: A repository declares which work may start without asking

Keel MUST read an optional `triage:` declaration from `keel/config.yaml` naming what admits an issue
into the pipeline without asking the owner. An absent, empty, or undeclared block MUST admit nothing.

The declaration MUST accept two independent sources, and MUST treat either as sufficient on its own:

- **Labels** the issue carries, and
- **Issue numbers** listed in the repository's own file.

The issue-number source exists because the label source records the owner's decision on the issue,
where the person who reported it can see it and is implicitly asked to reason about it. A repository
that accepts issues from outside has a classification vocabulary there already, and an operational
switch is not part of it. The unit does not change: an issue number is applied by hand to one issue,
exactly as a label is, so the policy still admits a class curated one issue at a time rather than a
guess about which issues look easy. Keel MUST NOT infer admission from any property of an issue.

Both sources MUST be declarable in one block:

```yaml
triage:
  labels:
    - auto
  issues:
    - 62
```

A bare list written directly under `triage:` MUST continue to mean labels, unchanged, so that a
declaration written before the second source existed keeps its exact meaning. No entry that was
readable before MUST change what it admits.

`keel triage` MUST accept the issue's labels and the issue's number as supplied inputs, and MUST
require at least one of them rather than requiring labels specifically. Keel MUST NOT fetch either.

A repository's own admission list is a declaration the owner writes; Keel MUST NOT add to it, and an
unattended run MUST NOT widen it.

#### Scenario: A declared label admits an issue
- **WHEN** `keel/config.yaml` declares `triage:` accepting the label `auto` and an issue carrying
  that label is evaluated
- **THEN** Keel reports the issue admitted
- **AND THEN** the reason names the label that admitted it

#### Scenario: A declared issue number admits an issue
- **WHEN** `keel/config.yaml` declares `triage:` with `issues:` listing an issue's number and that
  issue is evaluated, carrying no accepted label
- **THEN** Keel reports the issue admitted
- **AND THEN** the reason names the number and that the repository's own declaration listed it,
  so a reader can tell which of the two sources answered

#### Scenario: A declaration written before the second source existed is unchanged
- **WHEN** `triage:` holds a bare list of labels with no `labels:` or `issues:` key
- **THEN** those entries are read as accepted labels and admit exactly the issues they admitted before
- **AND THEN** no entry in that list is read as an issue number

#### Scenario: Either source admits alone
- **WHEN** a repository declares both `labels:` and `issues:`
- **THEN** an issue matching either one is admitted
- **AND THEN** an issue matching neither is refused

#### Scenario: No declaration admits nothing
- **WHEN** `keel/config.yaml` declares no `triage:` block, or declares an empty one
- **THEN** every issue is refused
- **AND THEN** the refusal states that the repository has declared no triage policy, rather than
  implying the issue was judged unsuitable

#### Scenario: A refusal names the policy it failed
- **WHEN** an issue carrying no accepted label and holding no listed number is evaluated against a
  declared policy
- **THEN** the refusal names what the issue carried and both halves of what the declaration accepts
- **AND THEN** the reader can tell an unadmitted issue from an undeclared policy, and can tell a
  repository that declared only labels from one that declared only numbers

### Requirement: A triage declaration Keel cannot fully read admits nothing

A `triage:` block containing anything Keel does not recognize MUST admit nothing at all, and the
refusal MUST name the entries it could not read. Admitting the readable half would grant the entries
beside a typo while their author believes they granted the typo too — the same reason an
unrecognized `authorize:` action and an unrecognized `delegation:` tier already authorize nothing.

An `issues:` entry MUST be a bare positive integer. Any other spelling of a number, including one
written with a leading `#`, MUST be reported by name with the accepted form rather than guessed at.

#### Scenario: An unreadable entry refuses the whole policy
- **WHEN** `triage:` declares an `issues:` entry that is not a bare number, or a sub-key that is
  neither `labels:` nor `issues:`, or mixes a bare list with sub-keys
- **THEN** no issue is admitted, including one that matches an entry Keel did read
- **AND THEN** the refusal names the entry it could not read and the forms it accepts

#### Scenario: The unreadable refusal is not the undeclared refusal
- **WHEN** an unreadable declaration refuses an issue
- **THEN** the reason states that the declaration could not be read, distinct from the reason given
  when a repository has declared no policy at all
- **AND THEN** the owner can tell a broken declaration from an absent one without reading the file

### Requirement: The triage surface reports every declared source

`keel --doctor` MUST report the triage surface naming each declared source, so that "what may start
work here without asking" is answerable from one command rather than by reading the config file. A
repository declaring neither source MUST be reported as declaring none.

#### Scenario: Doctor names both sources
- **WHEN** a repository declares accepted labels and listed issue numbers
- **THEN** `keel --doctor` reports the triage surface naming the labels and the numbers
- **AND THEN** a repository declaring only one of the two names only that one

#### Scenario: Doctor reports an unreadable declaration as declaring nothing
- **WHEN** a repository's `triage:` block cannot be fully read
- **THEN** `keel --doctor` reports that no issue starts work unattended
- **AND THEN** it names what could not be read, rather than reporting the surface as undeclared

### Requirement: The triage command is discoverable from `--help`

`keel --help` MUST list `keel triage` in its `Usage:` block, naming both `--labels` and `--issue`,
so that the command's flags are discoverable from the terminal and not only from `README.md`.

#### Scenario: Help lists the triage command
- **WHEN** a user runs `keel --help`
- **THEN** the `Usage:` block includes a `keel triage` line
- **AND THEN** that line names both `--labels` and `--issue`

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
