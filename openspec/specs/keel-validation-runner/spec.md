# keel-validation-runner Specification

## Purpose
TBD - created by archiving change consolidate-and-parallelize-validation-runner. Update Purpose after archive.
## Requirements
### Requirement: One scenario registry drives all validation entry points

`validate_plugin.py` MUST own a single ordered scenario registry consumed by both the `--scenario <name>` dispatch and the `--all` runner. `package.json`'s test script MUST invoke the runner once and MUST NOT enumerate scenarios. A scenario that proves its own registration MUST assert registry membership, not `package.json` content.

#### Scenario: Adding a scenario registers once

- **WHEN** a new validator scenario is added to the registry
- **THEN** it is reachable via `--scenario <name>` and included in `--all`
- **AND THEN** `package.json` needs no edit

#### Scenario: Single-scenario CLI stays stable

- **WHEN** an archived or active task Verify command invokes `--scenario <name>`
- **THEN** the invocation, exit-code semantics, and output behavior match the pre-runner contract

#### Scenario: Unknown scenario still fails loudly

- **WHEN** `--scenario` names an unregistered scenario
- **THEN** the runner reports the unknown name and exits non-zero

### Requirement: The full run is parallel, deterministic, and fail-loud

`--all` MUST run the baseline validation and every registered scenario, MAY execute scenarios concurrently in isolated processes with bounded parallelism, MUST buffer per-scenario output and report results deterministically in registry order, and MUST complete the whole set before summarizing. Any failure MUST name the failing scenarios and exit non-zero. A scenario MAY report itself skipped, with exit code `3`, only because an external runtime it probes is absent; `--all` MUST count skips separately from passes, name each one with its reason, and MUST NOT treat a skip as a failure.

A tool this package declares as its own dependency is not an external runtime. The suite MUST resolve such a tool from the package's own installed dependencies before consulting `PATH`, because that is the version the repository is tested against and a different version that happens to be on `PATH` is answering for it. A checkout that has installed its dependencies MUST therefore run every scenario that probes one, rather than failing or skipping it.

A probe that cannot find the tool it needs MUST NOT report that as a failure of the subject it was probing. The two outcomes MUST carry their own messages: a tool that could not be resolved names the locations searched, and a tool that ran and refused reports what it said. One condition covering both names the wrong cause whenever the other one fires, and sends the reader to a subject that has nothing wrong with it.

#### Scenario: Parallel output never interleaves

- **WHEN** `--all` runs scenarios concurrently
- **THEN** each scenario's output is reported as one contiguous block in registry order
- **AND THEN** concurrency never changes pass/fail results relative to a sequential run

#### Scenario: One failure fails the run without hiding others

- **WHEN** at least one scenario fails during `--all`
- **THEN** the remaining scenarios still run
- **AND THEN** the summary names every failing scenario and the process exits non-zero

#### Scenario: Baseline validation is included

- **WHEN** `--all` runs
- **THEN** the baseline validation executes as part of the run
- **AND THEN** a baseline failure fails the run like a scenario failure

#### Scenario: An absent external runtime skips instead of failing

- **WHEN** a scenario's subject is a native runtime that is not installed on the host
- **THEN** it reports the skip with the runtime it needed and exits `3`, and `--all` reports the run as passing with that scenario named as skipped and excluded from the verified count
- **AND THEN** the same scenario still executes normally wherever that runtime is present

#### Scenario: Skipping is only for an absent runtime

- **WHEN** a scenario fails an assertion, cannot build a fixture, or behaves differently on the host platform
- **THEN** it fails, because the skip path is reserved for an absent external runtime
- **AND THEN** exit code `3` never stands for an unverified assertion

#### Scenario: A declared dependency is resolved from the package

- **WHEN** a scenario probes a CLI this package declares as a dependency, on a checkout that has installed its dependencies and has no such tool on `PATH`
- **THEN** the scenario runs, resolving the tool from the package's own installed dependencies
- **AND THEN** it neither fails nor skips for want of a `PATH` entry

#### Scenario: A tool that cannot be found is not a broken subject

- **WHEN** a probe cannot resolve the CLI it needs
- **THEN** it reports that the tool was not found and names the locations it searched
- **AND THEN** the message is distinct from the one a resolved tool's refusal produces, so the reader is not sent to a subject that has nothing wrong with it

### Requirement: The full gate runs on a clean CI runner

The validation suite MUST be runnable on a clean runner that has Node, Python, and the repository — and nothing else. Assertions MUST NOT depend on the host's path-separator spelling, and a scenario that cannot run because an external runtime is absent MUST report a skip rather than fail. Keel's own repository MUST run its full gate in continuous integration on every push and pull request, which is the CI half of the verification-layering split Keel already defines.

#### Scenario: Path assertions do not depend on the host separator

- **WHEN** a scenario asserts on a path that Keel printed through the host's path joiner
- **THEN** it normalizes the captured output's separators before comparing, and states the expected path with forward slashes
- **AND THEN** the same assertion holds on a POSIX runner and on Windows without branching on the platform

#### Scenario: The repository runs its own full gate in CI

- **WHEN** a commit is pushed or a pull request is opened
- **THEN** a workflow installs the pinned dependencies and runs the single `--all` entry point
- **AND THEN** the release workflow keeps its own tag-and-version guard and does not become the suite's only runner

### Requirement: Resident-block content is checked as topics, not as prose

The resident-block check MUST distinguish a required entry that names a command, marker, or identifier from one that states a topic in prose. A command or marker MUST be matched literally, so a rename fails the check. A topic MUST be matched by pattern, so the block's wording can be improved — which it must be, because the block is under a line and byte budget — without a validator edit. The diagnostic MUST name which kind of entry was missing.

#### Scenario: Rewording a topic keeps the check green

- **WHEN** a resident block states a required topic in different words while keeping its concepts in one statement
- **THEN** the check passes without any validator edit
- **AND THEN** the same holds for every caller of the check, not just the baseline run

#### Scenario: Deleting a topic still fails

- **WHEN** a required topic's statement is removed from the resident block
- **THEN** the check fails and names the missing topic
- **AND THEN** a rewrite that merely mentions one of the topic's words does not satisfy it

#### Scenario: Renaming a command still fails

- **WHEN** a required entry names a command, marker, or identifier and the block no longer contains it exactly
- **THEN** the check fails, because a resident block that names a command must name the one that exists
- **AND THEN** the diagnostic distinguishes this from a missing topic

### Requirement: A derived assertion set that collapses to empty fails instead of passing

Some scenarios assert over a set the validator derives at run time — the files a
packaged asset root contains, for example — rather than over a literal list. When
the derivation stops matching the repository layout, the set becomes empty, every
loop over it executes zero comparisons, and the scenario reports success. Nothing
about that outcome is distinguishable from real verification, and no reader is
prompted to look, because a check whose failure mode is silence never asks for
attention.

A helper that resolves a packaged asset root MUST fail, naming the path it
expected, when that root is absent; it MUST NOT return an empty set. A scenario
whose assertions are driven by such a derived set MUST fail when the set is
empty. The failure MUST identify the derivation, not merely report that an
assertion count was zero.

#### Scenario: A missing packaged asset root fails loudly

- **WHEN** a validator helper resolves a packaged asset root that does not exist
- **THEN** it fails and names the path it expected
- **AND THEN** it does not substitute an empty set that would let its callers pass

#### Scenario: An empty derived set is a failure, not a pass

- **WHEN** a scenario's assertions iterate a derived set that resolves to nothing
- **THEN** the scenario fails and identifies the derivation that produced nothing
- **AND THEN** the run does not report the scenario as verified

#### Scenario: The packaged schema install surface is actually verified

- **WHEN** the scenarios covering `keel --install`, `--uninstall`, and `--clear` assert on the packaged OpenSpec schema
- **THEN** they compare against the files the installer really reads, so a stop in writing or removing the schema fails the run
- **AND THEN** adding or renaming a packaged schema file changes what is asserted without a validator edit

#### Scenario: Retired distribution paths are not referenced

- **WHEN** the validator resolves a path under a distribution tree the repository asserts has been removed
- **THEN** that reference is a defect, because it can only ever resolve to nothing
- **AND THEN** the check that depended on it is either repointed at a real root or removed in favor of a check that runs

### Requirement: The suite does not write to the repository it validates

A validation run MUST leave the repository byte-identical. A scenario that
mutates the tree it is checking corrupts two things at once: it dirties an
author's working copy with changes unrelated to their work, and — the worse
half — it can satisfy the very condition another check is asserting. A check
whose input is produced by its own test run cannot fail, and is therefore not
verification, however green it reports.

Scenarios MAY invoke Keel against the repository root for read-only purposes.
A scenario MUST NOT invoke a mutating Keel command against the repository root;
where the behavior under test needs a repository of a particular shape, the
scenario MUST build a fixture with that shape. A scenario that runs an install
MUST assert what the install did **not** write, not only the one effect it came
to check.

#### Scenario: A run leaves the tree unchanged

- **WHEN** the full validation suite runs against a clean checkout
- **THEN** the repository is byte-identical afterwards
- **AND THEN** no marker, overlay, or generated surface is rewritten as a side effect of testing

#### Scenario: A mutating invocation against the repository root is refused

- **WHEN** a scenario passes the repository root to a Keel command that writes
- **THEN** the check fails, naming the scenario and the invocation
- **AND THEN** read-only invocations against the repository root remain legal

#### Scenario: Install behavior is proven on a fixture with the required shape

- **WHEN** a scenario needs Keel to classify a repository a particular way
- **THEN** it builds a fixture carrying the signals the classifier actually reads
- **AND THEN** it asserts both the effect under test and the absence of other writes

### Requirement: A narrowed refusal is asserted from both sides
When validation covers a diagnostic whose scope this project narrows, the suite MUST assert both the shape that must still be refused and the shape that must now pass. A scenario asserting only the newly passing shape MUST NOT be accepted as coverage, because a check that removed the refusal entirely would also satisfy it.

#### Scenario: A narrowed diagnostic keeps its refusing case
- **WHEN** a scenario covers a diagnostic whose matching scope was narrowed
- **THEN** it asserts that the still-in-scope shape is refused and names that diagnostic
- **AND THEN** it asserts that the out-of-scope shape produces no such diagnostic

#### Scenario: Following the diagnostic resolves the problem it reports
- **WHEN** a scenario covers a diagnostic that tells the author what to change
- **THEN** it applies exactly what the diagnostic names and asserts the same diagnostic no longer appears

### Requirement: A shipped template is validated by the tool that consumes it
Validation MUST assert each shipped schema template by filling its author-facing slots and running the tool that consumes its output — `openspec validate` for a spec template, the `task-start` gate for a tasks template — rather than by matching the template's prose. A prose assertion MUST NOT be accepted as coverage, because a template that only mentions a requirement in a comment satisfies it while still failing for the author who copies it.

#### Scenario: A copied template passes the gate that consumes it
- **WHEN** a shipped template's author-facing slots are filled with concrete text and the result is presented to the tool that consumes it
- **THEN** that tool reports no error
- **AND THEN** the assertion is made through that tool rather than by matching the template's own wording

#### Scenario: The template drifts from the rule it illustrates
- **WHEN** a shipped template's example no longer satisfies the gate that reads it
- **THEN** validation fails and names the diagnostics the filled template produced

#### Scenario: The consuming tool is unavailable
- **WHEN** a template's consuming tool is not on PATH
- **THEN** the scenario reports the skip rather than passing silently or failing

### Requirement: A shipped tasks template carries a worked example of every strategy shape it documents
A shipped tasks template MUST show a worked example of each Evidence shape its prose requires, not the prose alone. For a red-green strategy that means a concrete check carrying its bare, `.red`, and `.green` Evidence entries, and a `regression`-tagged check carrying only its bare entry, with at least one check left untagged.

#### Scenario: The red-green shape is shown, not only described
- **WHEN** an author reads the shipped tasks template to write a red-green task
- **THEN** the template shows a strategy line, an untagged check with its bare, `.red`, and `.green` Evidence entries, and a `regression`-tagged check with only its bare entry
- **AND THEN** the example passes `task-start` once its slots are filled

### Requirement: The one-message-many-failures assertion shape is counted

The validation suite MUST report how many assertion sites in `scripts/validate_plugin.py` guard several distinct failures behind one failure message, and MUST compare that number against a recorded count. The counted shape is an `if` whose body is one or more `report(...)` calls followed by exactly one `return`, whose test is an `or`, where at least one operand is a membership test and at least one operand is not.

The comparison MUST fail when the count rises, naming the sites that are not in the recorded set so the author sees which assertion they just wrote. It MUST also fail when the count falls without the recorded number being lowered, because a number that only rises-checks becomes false the first time a site is fixed.

Keel MUST NOT present the count as a defect count. The shape is a signal that one message covers more than one failure; whether a given message misleads is a semantic judgment that stays with `keel-review-checklist`.

#### Scenario: A newly added site fails the suite and is named
- **WHEN** an assertion of the counted shape is added to `scripts/validate_plugin.py`
- **THEN** the scenario fails, reports the count that was found against the recorded count, and names the added site
- **AND THEN** the recorded count is unchanged by the failure

#### Scenario: A stale recorded count fails when sites are fixed
- **WHEN** a counted site is split so that each failure carries its own message, and the recorded count is not lowered
- **THEN** the scenario fails and states that the recorded count is higher than what the file contains
- **AND THEN** lowering the recorded number to the measured one restores the pass

#### Scenario: The count is reported as a shape, not as defects
- **WHEN** the scenario reports the counted sites
- **THEN** the wording states that the count bounds a shape rather than asserting that each site is wrong

### Requirement: The published spec store is validated by the tool Keel ships

Validation MUST run the OpenSpec validator over the repository's own published spec store in strict mode and MUST fail naming each spec that did not pass, because the store is the artifact Keel asks every consumer to trust and no other check reads it. Validating a change validates the change; it says nothing about the specs the change was promoted into.

The assertion MUST be that no published spec fails. A tolerated failure count MUST NOT be recorded in place of it, since a recorded tolerance is a budget and a budget for failures is where the next one hides.

The check MUST state the validator version it exercised, so a result is attributable to the program that produced it, and MUST report a skip rather than a pass when no validator resolves.

#### Scenario: A published spec that fails strict validation fails the suite
- **WHEN** validation runs and a spec in the published store does not pass strict validation
- **THEN** the suite fails naming that spec
- **AND THEN** the failure is not absorbed into a recorded count of known failures

#### Scenario: The store is asserted rather than a change
- **WHEN** validation covers strict spec validation
- **THEN** the assertion reads the published spec store
- **AND THEN** validating a change is not accepted as coverage of the store

#### Scenario: The validator that answered is named
- **WHEN** the strict store validation reports its result
- **THEN** it states the validator version it exercised

#### Scenario: No validator resolves
- **WHEN** no OpenSpec validator can be resolved
- **THEN** the scenario reports the skip rather than passing silently

### Requirement: A scenario name written into an active task contract is checked against the registry

A task's `Verify` block names the scenarios its checks will run, and a name the registry does not hold makes that check unrunnable while the contract still reads as covered. Validation MUST read the `tasks.md` of every active change and MUST fail when a scenario reference names a scenario that is not registered, reporting the file, the 1-indexed line, and the name.

Two reference forms MUST be recognized: a name following `--scenario`, and a backticked lowercase token inside a `Verify` or `Commands` `M<n>` check whose text asserts that something stays green. Both forms carry no false positive against every task contract this repository has written, and that is the reason they are the recognized ones. Validation MUST NOT read every backticked token in a check as a scenario reference: gate stages, diagnostic codes, skill names, capability names, and hook events share the same spelling, and a check that reports them would be wrong more often than right.

Archived changes MUST NOT be scanned. An archived task records what was true when it ran, and a scenario renamed afterwards is not a defect in the record.

The check MUST be able to fail when the active set is empty. A run whose assertions all came from a set that resolved to nothing is indistinguishable from a run that verified something, so the recognized forms MUST be asserted against content the scenario controls, and not only against whatever the working tree happens to contain.

#### Scenario: An unregistered name in a regression check fails the suite
- **WHEN** an active change's `Verify` block declares a check asserting that a backticked name stays green, and no scenario by that name is registered
- **THEN** validation fails, naming the `tasks.md`, the line, and the name
- **AND THEN** the message states the two forms that are read as scenario references

#### Scenario: An unregistered name after `--scenario` fails the suite
- **WHEN** an active change's `tasks.md` names a scenario after `--scenario` and no scenario by that name is registered
- **THEN** validation fails, naming the file, the line, and the name

#### Scenario: Vocabulary that is not a scenario name is left alone
- **WHEN** a check names a gate stage, a diagnostic code, a skill, a capability, or a hook event in backticks
- **THEN** validation reports nothing, because those are not scenario references
- **AND THEN** a registered scenario named in either recognized form also reports nothing

#### Scenario: Archived changes are not scanned
- **WHEN** an archived change's `tasks.md` names a scenario that is no longer registered
- **THEN** validation reports nothing, because renaming a scenario does not make a completed record wrong

#### Scenario: An empty active set does not stand in for verification
- **WHEN** the repository has no active change, which is its normal state between changes
- **THEN** the scenario still asserts each recognized form against content it controls, and fails if the extractor stops reporting a planted unregistered name
- **AND THEN** the run does not report the check as verified on the strength of an empty scan
