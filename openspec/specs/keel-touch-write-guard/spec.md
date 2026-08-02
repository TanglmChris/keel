# keel-touch-write-guard Specification

## Purpose
TBD - created by archiving change enforce-touch-write-guard. Update Purpose after archive.
## Requirements
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

### Requirement: Repository containment is decided on resolved paths

The write guard MUST decide whether a target is inside the guarded repository by comparing paths with symbolic links resolved on both sides. One file MUST get one answer however its path is spelled, so a target reached through a symbolic link MUST NOT escape the guard that denies the same file reached directly.

When the target does not yet exist, Keel MUST resolve the nearest existing ancestor and compare the remainder against it, because a guarded write is usually a file that is about to be created. When no ancestor resolves, Keel MUST fall back to the unresolved comparison rather than failing open or closed on an unreadable directory.

The helper baseline check MUST answer the same question the same way, so a baseline path inside the worktree is refused whether or not the worktree is reached through a link.

#### Scenario: A symlinked path does not escape the guard
- **WHEN** a guarded task's manifest is active and a write targets a file outside Touch through a symbolic link to the repository
- **THEN** the guard denies it, exactly as it denies the same file named by its resolved path
- **AND THEN** a write inside Touch is still allowed through either spelling

#### Scenario: A file that does not exist yet is still placed
- **WHEN** a guarded write targets a path that has not been created
- **THEN** containment is decided from the nearest existing ancestor
- **AND THEN** a new file inside Touch is allowed and a new file outside Touch is denied

#### Scenario: A helper baseline inside a linked worktree is refused
- **WHEN** a helper baseline path resolves inside the repository worktree, reached through a symbolic link
- **THEN** the capture is refused
- **AND THEN** a baseline that genuinely resolves outside the worktree is still accepted

### Requirement: A manifest whose change is gone is refused as stale

The write guard MUST distinguish a manifest pointing at a change directory that no longer exists from one whose task it merely cannot match inside a live `tasks.md`. The second is a parse miss the guard MUST continue to refuse to guess about; the first is a fact, and the guard MUST state it.

Keel MUST keep denying the write. Failing closed is what stops archiving a change from silently disabling the guard, so the outcome does not change — only what the refusal says. The message MUST name the action that resolves the state it is refusing, and MUST NOT direct the reader to reauthorize a task that no longer exists.

#### Scenario: An archived change's manifest denies by naming the clear
- **WHEN** a manifest is active and its change directory has been archived
- **THEN** the guard denies the write and reports the manifest as stale, naming `keel guard clear`
- **AND THEN** it does not tell the reader to reauthorize the vanished task through `keel gate task-start`

#### Scenario: A task missing from a live tasks.md is unchanged
- **WHEN** a manifest's change directory exists but its task id is absent from `tasks.md`
- **THEN** the guard behaves exactly as it did before this requirement, enforcing Touch
- **AND THEN** the stale-manifest message is not produced
