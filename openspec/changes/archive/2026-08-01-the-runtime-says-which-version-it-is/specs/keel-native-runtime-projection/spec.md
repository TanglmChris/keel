## ADDED Requirements

### Requirement: The session projection reports runtime version alignment

Keel MUST compare the version of the plugin executing the SessionStart hook, the version of the `keel` CLI it invokes, and the protocol version stamped in the repository's managed block, and MUST report a disagreement on both the human channel and the model payload. Comparison MUST be exact string equality, MUST be local and offline, and MUST NOT consult any remote source for a newer release.

#### Scenario: A stale runtime is reported on both channels
- **WHEN** the executing plugin, the CLI, and the repository's stamped protocol version are not all equal
- **THEN** the projection names each discovered version and states that they disagree
- **AND THEN** the statement appears on the human channel as well as the model payload, because updating the runtime is the person's action

#### Scenario: An aligned runtime says nothing
- **WHEN** every discoverable version is equal
- **THEN** the projection adds no version line to either channel
- **AND THEN** the rest of the projection is byte-identical to what it would have been without this capability

#### Scenario: A mismatch names the restart requirement
- **WHEN** a version disagreement is reported
- **THEN** the report states that a session's hooks are fixed at session start, so an updated plugin applies only after restarting
- **AND THEN** a reader who updates and sees the same session unchanged is not left concluding the check is broken

### Requirement: An undiscoverable version is not reported as drift

Keel MUST distinguish a version it could not discover from a version that disagrees. An undiscoverable version MUST NOT by itself produce a report, and MUST NOT be treated as a mismatch. Keel MUST still compare whichever versions are discoverable.

#### Scenario: A repository with no managed block stays silent
- **WHEN** the repository's protocol version cannot be found and the plugin and CLI versions agree
- **THEN** the projection adds no version line
- **AND THEN** the absent protocol version is not reported as a disagreement

#### Scenario: Discoverable versions are still compared
- **WHEN** one version cannot be discovered and two that can disagree
- **THEN** the projection reports the disagreement between the two it could read
- **AND THEN** it names the third as undiscovered rather than silently including it in the comparison

#### Scenario: An unreadable plugin manifest does not fail the projection
- **WHEN** the plugin's own manifest is missing or unreadable
- **THEN** the projection still delivers its status, selection, and next action
- **AND THEN** no version comparison failure degrades or blocks the continuity report

### Requirement: Keel reports runtime versions and does not manage them

Keel MUST NOT install, update, pin, or resolve a plugin or CLI version, and MUST NOT offer to. Its scope over the runtime is limited to reporting what it observes and naming the host command the reader may choose to run.

#### Scenario: The report does not act
- **WHEN** a version disagreement is reported
- **THEN** Keel performs no installation, update, or version resolution
- **AND THEN** any remedy it names is the host's own documented command, presented as the reader's decision
