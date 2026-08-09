## MODIFIED Requirements

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
unattended run MUST NOT widen it. A surface other than `keel/config.yaml` and the unattended-run
protocol itself — such as the `keel-align-expectations` skill — MAY point to the protocol's
statement of the two sources instead of repeating it, provided the protocol itself still states
both in full.

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

#### Scenario: A secondary surface points instead of repeating

- **WHEN** a surface other than `keel/config.yaml` and the unattended-run protocol, such as the
  `keel-align-expectations` skill, needs to state how the two admission sources work
- **THEN** it may point to the protocol's own statement instead of restating it
- **AND THEN** `keel/config.yaml`'s comments and the protocol's own statement remain complete, so
  the pointer has a stable target

### Requirement: An unattended run may open a pull request and may not merge

Keel MUST state that an unattended run may triage, author, implement, verify, and open a pull
request, and MUST NOT merge one. Merging MUST remain a human act regardless of any declaration. A
secondary surface MAY point to that statement instead of repeating its exact wording, provided the
statement itself remains fully stated at the surface being pointed to.

#### Scenario: The boundary is stated where a run can read it

- **WHEN** the unattended-run protocol is inspected
- **THEN** it states that opening a pull request is permitted and merging is not
- **AND THEN** no configuration key grants a merge

#### Scenario: Standing authorization does not imply merge

- **WHEN** a repository standing-authorizes `push` and declares a triage policy
- **THEN** an unattended run may push and open a pull request
- **AND THEN** it still may not merge, because no declaration in Keel authorizes one

#### Scenario: A secondary surface points instead of repeating

- **WHEN** a surface other than the unattended-run protocol itself, such as the
  `keel-align-expectations` skill, needs to state this boundary
- **THEN** it may point to the protocol's own statement instead of restating its phrases
- **AND THEN** the protocol's own statement remains complete, so the pointer has a stable target
  and removing that target would surface as a missing statement there, not a silently absent
  boundary
