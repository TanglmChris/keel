## ADDED Requirements

### Requirement: Collect an explicitly reported result from the owned execution
The controller SHALL accept a result only from the exact completed native execution recorded for the current assigned task. An accepted result SHALL remain retrievable by the original todo ID. Receiving a result SHALL preserve existing worker permissions and task closure state.

#### Scenario: A read-only reviewer returns its result
- **WHEN** the current reviewer emits the requested final result envelope and the caller collects by todo ID
- **THEN** Keel persists the declared text once and the caller can read it after disconnecting the host

#### Scenario: A delayed execution no longer owns the task
- **WHEN** a previous thread, endpoint generation, mismatched turn or obsolete task supplies a result
- **THEN** Keel leaves the task without a newly accepted result
