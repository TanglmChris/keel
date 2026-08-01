## ADDED Requirements

### Requirement: The guard binds a delegated writer identically

The write guard MUST bind an authorized delegate's writes exactly as it binds the current agent's. The manifest scopes the repository and the task, not the identity of the process performing the write, so a delegate's in-repository write outside `Touch` MUST be denied with the same decision and the same reason the current agent receives.

#### Scenario: A delegate's out-of-Touch write is denied
- **WHEN** an authorized delegate edits an in-repository path outside the active manifest's `Touch`
- **THEN** the write is denied
- **AND THEN** the denial carries the same reason text the current agent receives for that path

#### Scenario: A delegate's in-Touch write proceeds
- **WHEN** an authorized delegate edits a path inside the active manifest's `Touch`
- **THEN** the write proceeds
- **AND THEN** the delegate's success is the control proving denial elsewhere is the guard acting rather than an unrelated inability to write

#### Scenario: Every manifest state applies to a delegate
- **WHEN** the manifest is invalid, its authority has drifted, or its task is already checked
- **THEN** a delegate's writes fail closed under that state exactly as the current agent's do
- **AND THEN** the repository-boundary passthrough still precedes every manifest-derived decision

#### Scenario: An absent manifest does not check a delegate
- **WHEN** no manifest is present and a delegate writes
- **THEN** the write passes through silently, because absence allows everything
- **AND THEN** that success is not evidence any write was checked, which is why delegation requires an active manifest before a delegate starts
