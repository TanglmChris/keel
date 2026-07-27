## MODIFIED Requirements

### Requirement: Guarded write tools outside Touch are denied deterministically
While a valid guard manifest is active on the Claude target, Keel MUST deny `Edit`, `Write`, and `NotebookEdit` tool calls whose resolved target path falls outside the manifest's normalized Touch list, and MUST allow calls inside the list without modifying their inputs. The guarded change's own `openspec/changes/<change>/` directory MUST additionally be writable without being declared in Touch, because it holds the records the task produces rather than the product it changes, and because the completion gate already refuses to attribute it as an outside-Touch failure. The guard and the completion gate MUST agree on that boundary.

#### Scenario: Out-of-Touch edit is denied
- **WHEN** a guarded session attempts a file-edit tool call targeting a path outside the normalized Touch list
- **THEN** the call is denied before execution
- **AND THEN** the denial names the exact offending path, the guarded change and task, and the clear or reauthorize commands

#### Scenario: In-Touch edit is untouched
- **WHEN** a guarded session attempts a file-edit tool call targeting a path inside the normalized Touch list
- **THEN** the call proceeds unmodified
- **AND THEN** the guard records no state change

#### Scenario: The guarded change's own records are writable undeclared
- **WHEN** a guarded session writes its own task's Evidence, Review, or checkbox, or any other path under the guarded change's `openspec/changes/<change>/` directory, without having declared it in Touch
- **THEN** the call proceeds, because those are the records the completion gate is waiting for rather than product writes
- **AND THEN** another change's directory, the archive tree, and every other path outside Touch are still denied

#### Scenario: Non-file-edit tools are unaffected
- **WHEN** a guarded session invokes tools other than the matched file-edit tools
- **THEN** the guard performs no interception
- **AND THEN** indirect write paths remain governed by resident-protocol discipline

### Requirement: Guard failure modes fail closed
A present guard manifest that cannot be trusted MUST deny guarded write tools instead of silently allowing them, and the denial MUST name a recovery path. Recorded content hashes MUST NOT be applied to the guarded change's own directory, because the capsule fingerprint excludes the checkbox and Evidence values and therefore already distinguishes a record write from a contract change. Denial after the guarded task is checked complete MUST be enforced directly on the task's checkbox rather than inferred from that directory's bytes.

#### Scenario: Invalid manifest denies
- **WHEN** the manifest exists but is unreadable, schema-invalid, or missing required fields
- **THEN** guarded file-edit calls are denied with a diagnostic
- **AND THEN** the diagnostic names `keel guard clear` and the reauthorization flow

#### Scenario: Authority drift denies
- **WHEN** the recorded authority content hashes no longer match the current files outside the guarded change's own directory, or fingerprint revalidation mismatches
- **THEN** guarded file-edit calls are denied
- **AND THEN** recovery requires returning through `task-start` and an explicit new `keel guard start`

#### Scenario: Recording progress is not authority drift
- **WHEN** a guarded task ticks its own checkbox or appends its own Evidence, changing the bytes of `openspec/changes/<change>/tasks.md`
- **THEN** the guard does not report authority drift and the task's remaining writes proceed
- **AND THEN** an edit in the same file that moves the compiled capsule fingerprint — Touch, Verify, Covers, or a boundary — is still reported as contract drift by the checks that compile the capsule

#### Scenario: Contract drift inside the change directory is caught where the capsule is compiled
- **WHEN** a guarded task edits its own contract — its Touch, Verify, Covers, title, or a boundary — without reauthorizing
- **THEN** `keel guard status` reports fingerprint drift and `keel gate task-complete` refuses the recorded anchor, because both compile the capsule and compare it
- **AND THEN** the write-time guard does not deny that task's next write on account of it, because a hook that cannot compile a capsule cannot separate a contract edit from a record write in the same file

#### Scenario: Completed task denies
- **WHEN** the guarded task's checkbox is already checked
- **THEN** guarded file-edit calls outside the record layer are denied, and `keel guard start` still refuses to authorize that task at all
- **AND THEN** the diagnostic directs the agent to clear the guard before any new authorization, while the task's own records stay writable so it can finish the Evidence its completion gate requires
