## ADDED Requirements

### Requirement: The interpreter and the OpenSpec binary that run are checked against what is required

Keel's Python runner MUST verify the version an interpreter reports against the minimum the suite requires, rather than accepting any interpreter whose `--version` exits successfully. When no candidate meets the minimum, it MUST name each interpreter it tried and the version that interpreter reported, so the reader's next action is installing one rather than debugging the failures a too-old interpreter produces.

`keel doctor` MUST report the resolved `openspec` command, the version it reports, and the range the repository declares, and MUST state when they disagree. Keel MUST NOT install, select, or refuse an OpenSpec version: reporting is the scope, as it is for the plugin and CLI versions.

Validation MUST assert the OpenSpec version it is exercising, because a suite that silently changes which program it runs reports facts about a different program.

#### Scenario: A too-old interpreter is named as the failure
- **WHEN** the only discoverable Python is older than the minimum the suite requires
- **THEN** the runner refuses with a message naming each interpreter tried and its reported version
- **AND THEN** it does not hand the suite an interpreter that will fail in unrelated places

#### Scenario: The OpenSpec binary in use is reported
- **WHEN** `keel doctor` runs
- **THEN** it reports the resolved `openspec` command, its version, and the declared range
- **AND THEN** a resolved version outside the declared range is stated rather than absorbed

#### Scenario: Validation states the OpenSpec version it tested against
- **WHEN** the suite runs against an `openspec` outside the range the repository declares
- **THEN** it fails naming both versions
- **AND THEN** the failure is one accurate message rather than a validation error about the artifact under test
