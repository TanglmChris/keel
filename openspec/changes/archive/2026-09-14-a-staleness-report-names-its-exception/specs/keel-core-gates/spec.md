## MODIFIED Requirements

### Requirement: A re-record may carry what the author declares survived it

`keel gate task-start --record` MUST accept a declaration naming the checks whose evidence the
author states the contract change did not affect.

When a re-record lands a different fingerprint, Keel MUST report which checks remain stale and,
when a declaration is given, which were declared unaffected and that the narrowing came from that
declaration. Keel MUST NOT report the declared checks as stale.

When a re-record lands a different fingerprint and **no** declaration is given, the report MUST
name the declaration as available, MUST state the condition under which it applies — that the
check's assertion did not move — and MUST state that the reason belongs in `Reauthorizations`.
Keel MUST NOT name which checks are unaffected, because it retains only the previous fingerprint
and cannot know. The report given **with** a declaration MUST NOT carry the suggestion, its
reader having already acted on it.

Keel MUST refuse a declaration naming anything that is not a check of the compiled contract, and
MUST refuse a declaration given without a re-record.

Keel MUST NOT verify that the declaration is true, and MUST NOT present it as verified: it does not
retain the previous capsule and cannot compare a check's former text to its current one. The
declaration MUST NOT change what completion requires.

#### Scenario: The warning names only what is still stale

- **WHEN** a re-record lands a different fingerprint and the author declares two of three checks unaffected
- **THEN** the report names the remaining check as stale
- **AND THEN** it names the declared checks and attributes the narrowing to the declaration

#### Scenario: The blanket warning names the declaration that narrows it

- **WHEN** a re-record lands a different fingerprint and no declaration is given
- **THEN** the report names `--keep-evidence`, states that it applies to a check whose assertion did not move, and states that the reason belongs in `Reauthorizations`
- **AND THEN** it names no check as unaffected

#### Scenario: The narrowed warning does not repeat the suggestion

- **WHEN** a re-record lands a different fingerprint and a declaration is given
- **THEN** the report does not suggest the declaration its reader just used

#### Scenario: A declaration names a check that does not exist

- **WHEN** a declaration names something the compiled contract does not declare as a check
- **THEN** `task-start` refuses it

#### Scenario: A declaration without a re-record is refused

- **WHEN** a declaration is given without a re-record
- **THEN** `task-start` refuses it

#### Scenario: Completion is unchanged

- **WHEN** a task completes after a declaration was made
- **THEN** every `M<n>` still requires its own Evidence, red-green still applies, and the semantic Review still runs

### Requirement: A recorded anchor is compared against the recompiled fingerprint

`task-complete` MUST recompile the selected task's capsule and compare the result with the fingerprint recorded in its Evidence `Contract` anchor. A difference MUST fail the gate. It MUST NOT be reported as a warning or as `needs-review`, because drift returns the task to authoring rather than to the judgment of the agent recording its own Review.

The diagnostic MUST name the recorded value, the recompiled value, and the command that reauthorizes the task, and MUST state that execution evidence produced under the previous contract is stale. Having named that command, it MUST also name the declaration that command accepts for a check whose assertion did not move.

Keel MUST NOT require the anchor to carry a capsule schema prefix. A fingerprint is a digest over the canonical capsule serialization, so a value that matches could only have come from the schema that produced it; the prefix is diagnostic detail, not a gate condition.

#### Scenario: A contract edited after recording is refused
- **WHEN** a task's Touch, Verify, Covers, or a boundary is changed after its anchor was recorded, and `task-complete` evaluates it
- **THEN** the gate fails with a contract-drift diagnostic
- **AND THEN** the diagnostic names both the recorded and the recompiled fingerprint, names the reauthorization command, and states that evidence recorded under the previous contract is stale

#### Scenario: The drift refusal names the declaration its own command accepts
- **WHEN** a contract-drift diagnostic names `keel gate task-start --record`
- **THEN** it also names `--keep-evidence` and the condition under which it applies

#### Scenario: An anchor holding a foreign fingerprint is refused
- **WHEN** the recorded anchor is a well-formed digest that the task's own capsule does not compile to
- **THEN** the gate fails rather than accepting the anchor on its shape
