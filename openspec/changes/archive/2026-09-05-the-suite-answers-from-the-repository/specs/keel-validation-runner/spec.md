## MODIFIED Requirements

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
