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
