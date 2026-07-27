## ADDED Requirements

### Requirement: Doctor reports the CLI resolution hazard in Keel's own repository

An author changing Keel's own gate, contract, or capability code runs gate commands against a CLI that may not be the code under change: a bare `keel` resolves to the installed package, not to the working tree. The failure mode is a silently stale result rather than an error, so `keel --doctor` MUST report the hazard and the working invocation when — and only when — it runs in Keel's own source repository.

#### Scenario: Source repository is told to use its own CLI
- **WHEN** `keel --doctor` runs in Keel's own source repository
- **THEN** it reports that gate commands verify the installed CLI unless invoked through the repository's own entry point, and names that invocation including the explicit repository argument it requires
- **AND THEN** the line is advisory, and reports no failure

#### Scenario: A consuming project is not shown the hazard
- **WHEN** the same command runs in a project that consumes Keel
- **THEN** the line is absent, because the installed CLI is the code under test there and the hazard does not exist
