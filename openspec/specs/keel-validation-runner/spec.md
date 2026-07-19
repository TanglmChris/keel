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

`--all` MUST run the baseline validation and every registered scenario, MAY execute scenarios concurrently in isolated processes with bounded parallelism, MUST buffer per-scenario output and report results deterministically in registry order, and MUST complete the whole set before summarizing. Any failure MUST name the failing scenarios and exit non-zero.

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

