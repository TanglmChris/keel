## ADDED Requirements

### Requirement: Drift names its cause when Git ties the anchor to a commit

`task-start --record` MUST write the running Keel version beside the fingerprint in the `Contract` anchor, as `(keel <version>)`; every reader MUST still accept an anchor without it. When a recorded anchor differs from the recompiled fingerprint, the gates and `keel context` MUST find the newest commit whose `tasks.md` for the change contains the recorded digest, compile that commit's task sources with the running compiler, and report the cause:

- when that compile reproduces the recorded digest, the capsule fields that changed since that commit, naming the commit;
- when it does not, the anchor names a Keel version other than the running one, and the commit compiles to today's fingerprint, a compiler change, naming the commit and both versions, and stating that no `--keep-evidence` is needed;
- otherwise the drift message without any cause, claiming nothing.

A compiler change MUST still fail the gate and name `keel gate task-start --record`. A Git or compile failure during diagnosis MUST yield no cause and MUST NOT turn into a gate error.

#### Scenario: A compiler change is named as one
- **WHEN** a task's committed sources compile to today's fingerprint, its anchor holds another digest, and the anchor names `keel 5.0.0`
- **THEN** `task-complete` fails with contract drift naming a compiler change, the recording commit, `5.0.0`, and the running version, and says no `--keep-evidence` is needed

#### Scenario: An edit is named by the field it changed
- **WHEN** a task's anchor was recorded and committed, and its Touch is then edited
- **THEN** `task-complete` fails with contract drift naming `touch` and the recording commit

#### Scenario: An anchor no commit explains claims nothing
- **WHEN** a task's anchor holds a digest its committed sources do not compile to, and names the running Keel version
- **THEN** `task-complete` fails with contract drift that names no cause and no changed field

## MODIFIED Requirements

### Requirement: A recorded anchor is compared against the recompiled fingerprint

`task-complete` MUST recompile the selected task's capsule and compare the result with the fingerprint recorded in its Evidence `Contract` anchor. A difference MUST fail the gate. It MUST NOT be reported as a warning or as `needs-review`, because drift returns the task to authoring rather than to the judgment of the agent recording its own Review.

The diagnostic MUST name the recorded value, the recompiled value, and the command that reauthorizes the task, and MUST state that execution evidence produced under the previous contract is stale, unless the drift is diagnosed as a compiler change, where it MUST instead state that the evidence stands. Having named that command, it MUST also name the declaration that command accepts for a check whose assertion did not move.

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

### Requirement: A re-record may carry what the author declares survived it

`keel gate task-start --record` MUST accept a declaration naming the checks whose evidence the
author states the contract change did not affect.

When a re-record lands a different fingerprint, Keel MUST report which checks remain stale and,
when a declaration is given, which were declared unaffected and that the narrowing came from that
declaration. Keel MUST NOT report the declared checks as stale.

When a re-record lands a different fingerprint and **no** declaration is given, the report MUST
name the declaration as available, MUST state the condition under which it applies — that the
check's assertion did not move — and MUST state that the reason belongs in `Reauthorizations`.
Keel MUST NOT name which checks are unaffected, because it cannot know which assertions moved,
unless the drift is diagnosed as a compiler change (see "Drift names its cause when Git ties the
anchor to a commit"): then the report MUST say the evidence stands, name the commit it was verified
against, and name no check as stale. The report given **with** a declaration MUST NOT carry the suggestion, its
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

#### Scenario: A compiler-only re-record keeps the evidence, verified

- **WHEN** a task's drift is diagnosed as a compiler change and `task-start --record` re-records it with no declaration
- **THEN** the report says the evidence stands, names the recording commit and both Keel versions, and names no check as stale

### Requirement: change-close compares the anchor of every checked task

`change-close` MUST compare each checked task's recorded anchor against its recompiled fingerprint, and MUST fail on a difference, except a difference diagnosed as a standing-authorization change, which MUST pass with a warning naming the task, because the task completed under the authorization it recorded. A checked task that records no anchor MUST also fail, because an absent record and a drifted one are the same absence of proof at the gate that closes a live change.

The close diagnostic MUST identify the task and MUST NOT direct the reader to complete a task that is already checked.

#### Scenario: Drift introduced after completion is caught at the close
- **WHEN** every task is checked, a task's contract is then edited without reauthorizing, and `change-close` runs
- **THEN** the gate fails and names the task whose anchor no longer matches

#### Scenario: A checked task with no anchor fails the close
- **WHEN** a checked task's Evidence `Contract` anchor holds no compiled fingerprint and `change-close` runs
- **THEN** the gate fails rather than closing a change whose completion cannot be verified
- **AND THEN** the diagnostic does not tell the reader to complete a task that is already complete

#### Scenario: An unchanged change closes as before
- **WHEN** every checked task's anchor matches its recompiled fingerprint
- **THEN** the anchor comparison contributes no problem

#### Scenario: A standing-authorization change does not drift a completed task

- **WHEN** a checked task inherits the standing authorization, its anchor and sources were committed, `keel/config.yaml` then replaces `push:main` with `push-protected:main`, and `change-close` runs
- **THEN** the gate passes and warns naming the task and the standing authorization
- **AND THEN** `task-complete` on an unchecked task inheriting the same change still fails with contract drift
