# keel-touch-write-guard Specification

## Purpose
TBD - created by archiving change enforce-touch-write-guard. Update Purpose after archive.
## Requirements
### Requirement: Guarded write tools outside Touch are denied deterministically
While a valid guard manifest is active on the Claude target, Keel MUST deny `Edit`, `Write`, and `NotebookEdit` tool calls whose resolved target path falls outside the manifest's normalized Touch list, and MUST allow calls inside the list without modifying their inputs.

#### Scenario: Out-of-Touch edit is denied
- **WHEN** a guarded session attempts a file-edit tool call targeting a path outside the normalized Touch list
- **THEN** the call is denied before execution
- **AND THEN** the denial names the exact offending path, the guarded change and task, and the clear or reauthorize commands

#### Scenario: In-Touch edit is untouched
- **WHEN** a guarded session attempts a file-edit tool call targeting a path inside the normalized Touch list
- **THEN** the call proceeds unmodified
- **AND THEN** the guard records no state change

#### Scenario: Non-file-edit tools are unaffected
- **WHEN** a guarded session invokes tools other than the matched file-edit tools
- **THEN** the guard performs no interception
- **AND THEN** indirect write paths remain governed by resident-protocol discipline

### Requirement: Guard failure modes fail closed
A present guard manifest that cannot be trusted MUST deny guarded write tools instead of silently allowing them, and the denial MUST name a recovery path.

#### Scenario: Invalid manifest denies
- **WHEN** the manifest exists but is unreadable, schema-invalid, or missing required fields
- **THEN** guarded file-edit calls are denied with a diagnostic
- **AND THEN** the diagnostic names `keel guard clear` and the reauthorization flow

#### Scenario: Authority drift denies
- **WHEN** the recorded authority content hashes no longer match the current files, or fingerprint revalidation mismatches
- **THEN** guarded file-edit calls are denied
- **AND THEN** recovery requires returning through `task-start` and an explicit new `keel guard start`

#### Scenario: Completed task denies
- **WHEN** the guarded task's checkbox is already checked
- **THEN** guarded file-edit calls are denied
- **AND THEN** the diagnostic directs the agent to clear the guard before any new authorization

### Requirement: Guard lifecycle is bounded by one task
One guard manifest MUST cover exactly one task, clearing MUST be explicit, and no guard state may carry over into another task's authorization.

#### Scenario: Clear is explicit
- **WHEN** the current agent runs `keel guard clear`
- **THEN** the manifest is removed and enforcement stops
- **AND THEN** read-only gates never delete the manifest themselves

#### Scenario: Completion reminds, does not clean
- **WHEN** `keel gate task-complete` passes while a guard manifest is active
- **THEN** the gate output reminds the agent to clear the guard
- **AND THEN** the gate itself writes nothing

#### Scenario: New task requires new activation
- **WHEN** a guard manifest for one task exists and the agent starts another task
- **THEN** the existing guard supplies no authority for the new task
- **AND THEN** guarding the new task requires an explicit clear or forced restart with a new fingerprint

### Requirement: The guard manifest is declared ignorable local state

The write-guard manifest is per-clone session state, not project content. Keel's install and init paths MUST declare it ignorable so an ordinary gate run leaves no undeclared untracked file, and MUST do so without overwriting a project's own ignore file.

#### Scenario: Install declares the manifest ignorable
- **WHEN** `keel --install` or `keel --init` runs in a project with no `keel/.gitignore`
- **THEN** it scaffolds one declaring the guard manifest
- **AND THEN** a subsequent passing `task-start` leaves no undeclared untracked path behind

#### Scenario: An existing ignore file is not overwritten
- **WHEN** the project already has a `keel/.gitignore`
- **THEN** install leaves that file byte-identical and writes nothing into it, the same scaffold-once treatment `keel/config.yaml` already receives

### Requirement: Guard capability is reported from observed evidence
Keel MUST report the write-guard surface per target from observed evidence, MUST NOT claim `enforced` without behavioral probe evidence, and MUST state the enforcement boundary honestly. The guard command's own result MUST carry that boundary too, so a written manifest is never read as observed enforcement.

#### Scenario: Doctor reports the guard surface
- **WHEN** `keel --doctor` runs for the Claude target
- **THEN** it reports the guard hook surface, manifest state, and capability level derived from observed evidence
- **AND THEN** hook-file presence alone reports advisory, not enforced

#### Scenario: Guard status describes the manifest, not enforcement
- **WHEN** `keel guard start` or `keel guard status` reports a written manifest
- **THEN** the result states that the status describes the manifest and that enforcement depends on a runtime hook Keel cannot observe from the repository
- **AND THEN** no wording in the result asserts that writes are currently being checked

#### Scenario: Unguardable writes are documented
- **WHEN** guard capability is reported or documented
- **THEN** the file-edit-tools-only boundary is stated explicitly
- **AND THEN** `Bash` and other indirect writes are identified as disciplinary, not guarded

#### Scenario: Unsupported targets report manual
- **WHEN** the target is Codex or OpenCode
- **THEN** the guard capability reports manual with the reason
- **AND THEN** no unverified native enforcement claim is made

### Requirement: Write guard activation defaults to a passing task-start and stays task-scoped and fingerprinted

On the Claude target, a passing `keel gate task-start` MUST write the `keel-write-guard/v1` manifest for the selected task by default, binding it to that task's capsule fingerprint, normalized Touch list, and authority content hashes. The caller MUST be able to opt out with `--no-guard`, and `keel guard start` MUST remain available for explicit activation. The manifest MUST remain a disposable enforcement pointer and MUST NOT act as selection, continuity, or completion authority.

#### Scenario: Passing task-start records the manifest by default
- **WHEN** the current agent runs `keel gate task-start` for one selected task on the Claude target and compilation passes without `--no-guard`
- **THEN** Keel writes a `keel-write-guard/v1` manifest recording the change, task, capsule fingerprint, normalized Touch, and authority content hashes
- **AND THEN** no other Keel-owned session state is created

#### Scenario: Opt-out and non-Claude targets are unchanged
- **WHEN** the caller passes `--no-guard`, or the target has no guard-capable surface
- **THEN** `task-start` writes no manifest
- **AND THEN** enforcement remains resident-protocol discipline exactly as before

#### Scenario: Non-pass writes nothing
- **WHEN** `task-start` compilation fails or returns `needs-review`
- **THEN** no manifest is written, replaced, or cleared
- **AND THEN** any existing valid manifest for a previously authorized task is left untouched

#### Scenario: Task switch replaces the manifest
- **WHEN** a passing default-guarded `task-start` selects a different task than the active manifest
- **THEN** the manifest is replaced with the newly authorized task's binding
- **AND THEN** no guard stacking or multi-task manifest is introduced

#### Scenario: Absent manifest changes nothing
- **WHEN** no guard manifest exists in the project
- **THEN** file-edit tool calls proceed without Keel enforcement
- **AND THEN** Keel adds no warnings, prompts, or context demanding activation

#### Scenario: Guard manifest never selects work
- **WHEN** `keel context` or any continuity computation runs while a guard manifest exists
- **THEN** selection derives only from explicit choice, HANDOFF override, and OpenSpec state
- **AND THEN** the manifest contributes at most an informational warning

