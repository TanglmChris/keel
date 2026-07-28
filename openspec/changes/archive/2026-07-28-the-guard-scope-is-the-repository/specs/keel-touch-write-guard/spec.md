## ADDED Requirements

### Requirement: The guard's scope is the repository it was started in
A resolved target path that falls outside the repository root MUST pass through the write guard, and that decision MUST precede every manifest-derived decision — including the invalid-manifest denial, the authority-drift denial, and the completed-task denial. The boundary is computed from the event's working directory and target path alone and MUST NOT depend on reading, parsing, or validating the manifest, because a path outside the repository is not a product write the manifest has any authority over.

#### Scenario: An out-of-repository path passes while the manifest is invalid
- **WHEN** a guarded session edits a path outside the repository root and the manifest is unreadable or schema-invalid
- **THEN** the call proceeds
- **AND THEN** every in-repository path is still denied in that same state

#### Scenario: An out-of-repository path passes while authority has drifted
- **WHEN** a guarded session edits a path outside the repository root and recorded authority hashes no longer match
- **THEN** the call proceeds
- **AND THEN** an in-Touch path is still denied for that drift

#### Scenario: The boundary needs no manifest
- **WHEN** the guard decides whether a target lies outside the repository
- **THEN** it uses only the event's working directory and target path

## MODIFIED Requirements

### Requirement: Guarded write tools outside Touch are denied deterministically
While a valid guard manifest is active on the Claude target, Keel MUST deny `Edit`, `Write`, and `NotebookEdit` tool calls whose resolved target path lies inside the repository and falls outside the manifest's normalized Touch list, and MUST allow calls inside the list without modifying their inputs. A target outside the repository is out of the guard's scope and is governed by the repository-scope requirement instead. The guarded change's own `openspec/changes/<change>/` directory MUST additionally be writable without being declared in Touch, because it holds the records the task produces rather than the product it changes, and because the completion gate already refuses to attribute it as an outside-Touch failure. The guard and the completion gate MUST agree on that boundary.

#### Scenario: Out-of-Touch edit is denied
- **WHEN** a guarded session attempts a file-edit tool call targeting an in-repository path outside the normalized Touch list
- **THEN** the call is denied before execution
- **AND THEN** the denial names the exact offending path, the guarded change and task, and the clear or reauthorize commands

#### Scenario: In-Touch edit is untouched
- **WHEN** a guarded session attempts a file-edit tool call targeting a path inside the normalized Touch list
- **THEN** the call proceeds unmodified
- **AND THEN** the guard records no state change

#### Scenario: The guarded change's own records are writable undeclared
- **WHEN** a guarded session writes its own task's Evidence, Review, or checkbox, or any other path under the guarded change's `openspec/changes/<change>/` directory, without having declared it in Touch
- **THEN** the call proceeds, because those are the records the completion gate is waiting for rather than product writes
- **AND THEN** another change's directory, the archive tree, and every other in-repository path outside Touch are still denied

#### Scenario: Non-file-edit tools are unaffected
- **WHEN** a guarded session invokes tools other than the matched file-edit tools
- **THEN** the guard performs no interception
- **AND THEN** indirect write paths remain governed by resident-protocol discipline
