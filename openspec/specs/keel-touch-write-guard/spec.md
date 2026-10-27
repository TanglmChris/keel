# keel-touch-write-guard Specification

## Purpose
Define the write guard that holds file edits to a task's declared Touch: deterministic denial outside it, fail-closed behavior on any manifest fault, a lifecycle bounded by one fingerprinted task that a passing task-start begins by default, an ignorable local manifest, and capability reported only from observed evidence.
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
- **WHEN** a guarded session invokes tools other than the matched file-edit tools, other than a `Bash` call running `git push` while `push:<glob>` is declared
- **THEN** the guard performs no Touch interception
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
- **THEN** the file-edit-tools boundary is stated explicitly, with the one `Bash` exception: `git push` while `push:<glob>` is declared
- **AND THEN** every other `Bash` command and indirect write is identified as disciplinary, not guarded

#### Scenario: Unsupported targets report manual
- **WHEN** the target is Codex or OpenCode
- **THEN** the guard capability reports manual with the reason
- **AND THEN** no unverified native enforcement claim is made

#### Scenario: Standing warnings may be reworded for brevity without dropping an idea
- **WHEN** the durability and enforcement-boundary warning strings a guard result carries are edited for brevity
- **THEN** the result still states that the manifest is a disposable pointer and not durable authority, that OpenSpec and Git remain that authority, and that selection never derives from the manifest
- **AND THEN** the result still states that the reported status describes the manifest only, that enforcement is a runtime-hook fact Keel cannot observe, and that a written manifest is not evidence a write was checked
- **AND THEN** no wording asserts that enforcement is active, that enforcement is live, or that writes are guarded

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

### Requirement: Write-guard containment is decided on resolved paths

The write guard MUST decide whether a target is inside the guarded repository by comparing paths with symbolic links resolved on both sides, so one file gets one answer however its path is spelled. For a target that does not exist yet, Keel MUST resolve the nearest existing ancestor and compare the remainder; when no ancestor resolves, it MUST fall back to the unresolved comparison.

#### Scenario: A symlinked path does not escape the guard
- **WHEN** a guarded task's manifest is active and a write targets a file outside Touch through a symbolic link to the repository
- **THEN** the guard denies it, exactly as it denies the same file named by its resolved path
- **AND THEN** a write inside Touch is still allowed through either spelling

#### Scenario: A file that does not exist yet is still placed
- **WHEN** a guarded write targets a path that has not been created
- **THEN** containment is decided from the nearest existing ancestor
- **AND THEN** a new file inside Touch is allowed and a new file outside Touch is denied

### Requirement: A manifest whose change is gone is refused as stale

Keel MUST distinguish a manifest pointing at a change directory that no longer exists from one whose task it merely cannot match inside a live `tasks.md`. The second is a parse miss Keel MUST continue to refuse to guess about; the first is a fact, and Keel MUST state it.

This distinction MUST hold on every surface that reports the manifest's state — the write guard hook that refuses a write, and `keel guard status` that describes the manifest — and both MUST decide it by testing the same objects, the change directory and its archived copy, so that one surface cannot come to disagree with the other about a state a reader is looking at from both. A surface reporting the vanished change MUST carry a distinct problem code, so the two states are separable without matching on message text.

When the change directory is gone but `openspec/changes/archive/<date>-<change>/tasks.md` shows the guarded task checked, the task finished and its change was archived: the write guard MUST NOT decide the write, and `keel guard status` MUST report the status `archived` with the problem code `task-archived`, name the archived directory and `keel guard clear`, and exit 0. Otherwise Keel MUST keep denying the write. Failing closed is what stops archiving an unfinished task from silently disabling the guard, so the outcome does not change — only what the refusal says. The message MUST name the action that resolves the state it is refusing, and MUST NOT direct the reader to reauthorize a task that no longer exists.

A change directory that exists while its `tasks.md` does not MUST keep the parse-miss treatment. That is a live change mid-authoring, and reauthorizing it is genuinely its way out.

#### Scenario: An archived change's manifest denies by naming the clear
- **WHEN** a manifest is active and its change directory has been archived with the guarded task unchecked
- **THEN** the guard denies the write and reports the manifest as stale, naming `keel guard clear`
- **AND THEN** it does not tell the reader to reauthorize the vanished task through `keel gate task-start`

#### Scenario: A finished task's archived change no longer guards
- **WHEN** a manifest is active, its task is checked complete, and its change directory is moved to `openspec/changes/archive/<date>-<change>/`
- **THEN** a write to a product file and a write to a new change's `proposal.md` each get no decision from the guard
- **AND THEN** `keel guard status` exits 0 with status `archived` and problem code `task-archived`, naming the archived directory and `keel guard clear`

#### Scenario: A task missing from a live tasks.md is unchanged
- **WHEN** a manifest's change directory exists but its task id is absent from `tasks.md`
- **THEN** the guard behaves exactly as it did before this requirement, enforcing Touch
- **AND THEN** the stale-manifest message is not produced

#### Scenario: Guard status names the clear for an archived change
- **WHEN** `keel guard status` runs against a manifest whose change directory no longer exists and has no archived copy showing the task checked
- **THEN** it reports the manifest as stale, names the directory that is gone, and names `keel guard clear`
- **AND THEN** it does not direct the reader to reauthorize the vanished task, which `keel gate task-start` and `keel guard start` both refuse for a change that is not there

#### Scenario: Guard status is unchanged for a task missing from a live tasks.md
- **WHEN** `keel guard status` runs against a manifest whose change directory exists but whose task id is absent from `tasks.md`
- **THEN** it reports the same status, the same problem code, and the same message it reported before this requirement covered it
- **AND THEN** the two states no longer produce identical output

### Requirement: The manifest records what was dirty when the task started

The guard manifest MUST record the repository's dirty-path set at the moment `keel gate task-start` authorizes a task, alongside the fingerprint and Touch it already records. That record is what lets the completion gate attribute a later write to the task without a caller-supplied comparison base, and the moment it is taken is what makes it meaningful: any other moment answers a different question.

The recorded set MUST be produced by the same worktree reading the completion gate uses, so the two cannot disagree about which paths are dirty or how a rename is represented. It MUST be taken before the manifest itself is written, so the manifest never appears as a path the task authored.

Each recorded path MUST carry a content signature taken at that same moment — a hash of the path's content, or an explicit absent marker for a path with nothing to read. The signature is what lets the completion gate tell a path still holding the content it held at task start from one the task went on to change again; a bare path name cannot make that distinction, and MUST NOT be recorded alone.

The manifest remains disposable local state. A manifest carrying no such record MUST NOT be treated as recording an empty one, and the completion gate MUST fall back to unattributed reporting instead, because a missing record and a clean start are different facts and only one of them can be proved.

#### Scenario: The set is recorded when the task is authorized
- **WHEN** `keel gate task-start` writes the guard manifest for a task
- **THEN** the manifest records the dirty-path set observed at that moment
- **AND THEN** the manifest's own path is not part of that set

#### Scenario: The recorded set carries a content signature
- **WHEN** `keel gate task-start` records a dirty path
- **THEN** the manifest carries that path's content signature alongside its name
- **AND THEN** a path with nothing to read at that moment records an explicit absent signature rather than omitting the entry or recording the path name alone

#### Scenario: A manifest without the record does not claim a clean start
- **WHEN** the completion gate reads a manifest carrying no recorded dirty-path set
- **THEN** it reports dirty paths without attributing them
- **AND THEN** it does not fail the task on paths it cannot attribute

### Requirement: The completion gate catches what the guard cannot intercept

Enforcement binds the host's file-writing tools, so a write issued by a shell command reaches the worktree without the guard seeing it. Keel MUST NOT claim otherwise, and MUST NOT rely on the guard alone to keep a task inside its Touch. The completion gate is where such a write is caught, and it MUST catch it in its default invocation rather than only when a caller requests the comparison.

#### Scenario: A shell-issued write outside Touch is caught at completion
- **WHEN** a task writes a file outside its Touch by a means the write guard does not intercept
- **AND WHEN** task completion runs in its default invocation
- **THEN** completion fails naming that path
- **AND THEN** the outcome does not depend on whether the guard observed the write

### Requirement: A push outside the declared branches is refused

While `keel/config.yaml` declares at least one `push:<glob>` entry, the Claude write guard MUST examine every `Bash` call for `git push` invocations, whether or not a task manifest is active and whether or not the rest of the `authorize:` declaration is valid, and MUST deny the call when any push's target branch matches no declared glob, naming the branch and the globs. It MUST determine a target from an explicit refspec — the destination of `src:dst`, `src` alone, `HEAD` as the current branch, `:dst` as a delete — or, with no refspec, from the branch's configured push destination. When it cannot determine a target — `--all`, `--branches`, `--mirror`, `--tags`, an option it does not know, shell expansion in the push, a tag refspec, or no configured push destination — it MUST deny the call and name `git push origin <branch>` as the form to use. When a `cd` or `pushd` precedes the push in the same call, whatever its refspec, it MUST deny the call, say that the directory changes before the push, and name `git -C <directory> push` as the form to use. A `Bash` call with no `git push`, and any call while no `push:<glob>` is declared, MUST pass unchanged. Codex keeps its `manual` guard capability.

#### Scenario: A push to a declared branch passes
- **WHEN** `push:claude/*` is declared and a `Bash` call runs `git add -A && git push -u origin claude/fix`
- **THEN** the call proceeds

#### Scenario: A push to main is refused without a task
- **WHEN** `push:claude/*` is declared, no guard manifest exists, and a `Bash` call runs `git push origin HEAD:main`
- **THEN** the call is denied, naming `main` and `claude/*`

#### Scenario: A push with no refspec uses the branch's push destination
- **WHEN** `push:claude/*` is declared and `git push` runs on a branch whose push destination is `origin/main`
- **THEN** the call is denied naming `main`, and the same command on a branch pushing to `origin/claude/fix` proceeds

#### Scenario: An undetermined target is refused with the explicit form
- **WHEN** `push:claude/*` is declared and a `Bash` call runs `git push --all origin`, or `git push origin "$BRANCH"`
- **THEN** the call is denied and the reason names `git push origin <branch>`

#### Scenario: A directory change before a push is refused with the -C form
- **WHEN** `push:claude/*` and `push-protected:main@chief` are declared in the session's repository, and a `Bash` call runs `cd <other repository> && git push <url> main:main`, or `cd <subdirectory> && git push origin claude/fix`
- **THEN** each call is denied, the reason names `git -C <directory> push` and does not name the role `chief`, and `git -C <other repository> push <url> main:main`, whose repository declares nothing, proceeds

#### Scenario: Nothing is checked without a push scope
- **WHEN** `authorize:` declares a bare `push`, or no `push` at all, and a `Bash` call runs `git push origin HEAD:main`
- **THEN** the guard does not intercept it

### Requirement: A push to a protected branch is asked, not refused

When `keel/config.yaml` declares `push-protected:` entries, the Claude write guard MUST check `git push` as it does for `push:`, whether or not `push:` is declared. A target matching a `push:` glob MUST pass, unless the push carries tags (see "A push that carries tags is a tag push"); otherwise a target matching a `push-protected:` glob MUST return `permissionDecision: "ask"` with a reason naming the branch, so the host asks the user to confirm that one call; any other target MUST be denied. Keel MUST NOT store an approval. When the matching entry names a role and the session is not bound to it, the push MUST be denied naming the role. When the event's `permission_mode` is `bypassPermissions` or `dontAsk`, a protected push MUST be denied naming the mode, because the host cannot be relied on to ask there.

#### Scenario: The coordinator is asked, once per push
- **WHEN** `push-protected:main@iecc-pm` is declared, the session is bound to `iecc-pm` in `default` mode, and runs `git push origin HEAD:main` twice
- **THEN** the guard returns `ask` naming `main` both times, and writes nothing

#### Scenario: Another role is refused
- **WHEN** the same push runs in a session bound to `rtl`
- **THEN** the guard denies it naming `iecc-pm`

#### Scenario: A mode that cannot ask is refused
- **WHEN** the coordinator's push runs with `permission_mode` `bypassPermissions`
- **THEN** the guard denies it naming the mode

#### Scenario: Other branches are unchanged
- **WHEN** `push:claude/*` and `push-protected:main` are declared
- **THEN** a push to `claude/fix` passes and a push to `release` is denied

### Requirement: A push that carries tags is a tag push

While `push:` or `push-protected:` entries are declared, the Claude write guard MUST treat a `git push` that carries annotated tags as a tag push. A push carries tags when the last of `--follow-tags` and `--no-follow-tags` in its arguments is `--follow-tags`, or, with neither, when `push.followTags` resolves to true for that command, counting the repository's config and every `git -c` the command passes. Such a push MUST NOT pass on a `push:` glob alone: when every target matches a `push-protected:` entry, it MUST take that entry's path — role limit, refusal in a mode that cannot ask, and `ask` — with a reason saying it also pushes annotated tags; otherwise it MUST be denied, naming the tag carriage and `--no-follow-tags`. A `git` command preceded by a `GIT_CONFIG*` environment assignment MUST be denied as a push whose target the guard cannot determine, naming the variable.

#### Scenario: A granted branch pushed with --follow-tags is refused
- **WHEN** `push:flow-*` is declared and a `Bash` call runs `git push --follow-tags origin flow-release`
- **THEN** the call is denied, and the reason names `--follow-tags` and `--no-follow-tags`

#### Scenario: Config that carries tags is refused the same way
- **WHEN** `push:flow-*` is declared and the repository sets `push.followTags=true`, and a `Bash` call runs `git push origin flow-release`, or `git -c push.followTags=true push origin flow-release` runs where it is unset
- **THEN** each call is denied, naming `push.followTags`

#### Scenario: Turning tag carriage off restores the branch push
- **WHEN** the same declaration holds and a call runs `git push --follow-tags --no-follow-tags origin flow-release`, or `git -c push.followTags=false push origin flow-release` where the repository sets it
- **THEN** the call proceeds

#### Scenario: The coordinator is asked about main with its tags
- **WHEN** `push:flow-*` and `push-protected:main@iecc-pm` are declared and the session bound to `iecc-pm` runs `git push --follow-tags origin main` in `default` mode
- **THEN** the guard returns `ask`, and the reason names `main` and annotated tags; the same push from a session bound to `rtl` is denied naming `iecc-pm`

#### Scenario: Environment config is not read past
- **WHEN** `push:flow-*` is declared and a call runs `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push origin flow-release`
- **THEN** the call is denied naming `GIT_CONFIG_COUNT`

### Requirement: A redirection is never read as a push target

When the Claude write guard reads `git push` arguments from a `Bash` command, it MUST drop each shell redirection — `>`, `>>`, `<`, a file-descriptor prefix such as `2>`, a duplication such as `2>&1` or `>&2`, and `&>` — together with its target, and MUST NOT read any of them as a refspec or a remote.

#### Scenario: An in-scope push with redirections passes
- **WHEN** `push:flow-*` is declared and a `Bash` call runs `git push --dry-run origin HEAD:refs/heads/flow-probe 2>&1 | tail -1`, or the same with `2>/dev/null`, or `&> out.log`
- **THEN** the guard allows each

#### Scenario: An out-of-scope push with redirections is still refused
- **WHEN** the same declaration holds and a `Bash` call runs `git push origin HEAD:main 2>&1 | tail -1`
- **THEN** the guard denies it naming `main`, not a redirection
