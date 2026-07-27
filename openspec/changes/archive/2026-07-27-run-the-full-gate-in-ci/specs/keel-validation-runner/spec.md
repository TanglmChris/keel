## ADDED Requirements

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

## MODIFIED Requirements

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
