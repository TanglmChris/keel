## MODIFIED Requirements

### Requirement: The interpreter and the OpenSpec binary that run are checked against what is required

Keel's Python runner MUST verify the version an interpreter reports against the minimum the suite requires, rather than accepting any interpreter whose `--version` exits successfully. When no candidate meets the minimum, it MUST name each interpreter it tried and the version that interpreter reported, so the reader's next action is installing one rather than debugging the failures a too-old interpreter produces.

`keel doctor` MUST report the resolved `openspec` command, the version it reports, and the OpenSpec version declared by **the repository it names on its first line**, and MUST state when they disagree. It MUST read that declaration from the diagnosed repository and MUST NOT substitute Keel's own install location when the diagnosed repository declares none, because a diagnostic that answers about a different repository than the one it names is indistinguishable from one that agrees. Keel MUST NOT install, select, or refuse an OpenSpec version: reporting is the scope, as it is for the plugin and CLI versions. Which binary Keel resolves and runs is therefore unchanged by this requirement.

The reported declaration and the answering binary MUST be attributed to their sources, so a reader who sees two versions can tell which came from their repository and which from the program that answered. A repository declaring no OpenSpec version MUST be reported as declaring none, distinctly from a declaration that could not be read, and MUST NOT be reported as a disagreement.

Validation MUST assert the OpenSpec version it is exercising, because a suite that silently changes which program it runs reports facts about a different program. Coverage of this reporting MUST exercise a repository other than Keel's own source checkout, because that checkout is the one repository where Keel's install location and the diagnosed repository coincide, and it therefore cannot distinguish a diagnostic rooted at either.

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

#### Scenario: The declared version is read from the diagnosed repository
- **WHEN** `keel doctor` runs against a repository whose declared OpenSpec version differs from the one declared where Keel itself is installed
- **THEN** the openspec line reports the version declared by the diagnosed repository
- **AND THEN** it does not report the version declared where Keel is installed
- **AND THEN** the reported declaration is attributed to the repository rather than left for the reader to assign

#### Scenario: A repository declaring no OpenSpec version is reported as declaring none
- **WHEN** `keel doctor` runs against a repository that declares no OpenSpec version
- **THEN** the openspec line states that the repository declares none
- **AND THEN** it reports no disagreement and no warning arising from the absence
- **AND THEN** it does not report the absence as a failure to read

#### Scenario: The reporting is exercised from outside Keel's own checkout
- **WHEN** the suite covers which OpenSpec version `keel doctor` reports as declared
- **THEN** at least one check drives the diagnosis against a repository that is not Keel's source checkout and that carries its own declaration
- **AND THEN** a diagnostic rooted at Keel's install location fails that check rather than passing it
