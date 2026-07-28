## ADDED Requirements

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
