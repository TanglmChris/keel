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
- **WHEN** a guarded session invokes tools other than the matched file-edit tools, other than a `Bash` call running `git push` while `push:<glob>` is declared
- **THEN** the guard performs no Touch interception
- **AND THEN** indirect write paths remain governed by resident-protocol discipline

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

## ADDED Requirements

### Requirement: A push outside the declared branches is refused

While `keel/config.yaml` declares at least one `push:<glob>` entry, the Claude write guard MUST examine every `Bash` call for `git push` invocations, whether or not a task manifest is active and whether or not the rest of the `authorize:` declaration is valid, and MUST deny the call when any push's target branch matches no declared glob, naming the branch and the globs. It MUST determine a target from an explicit refspec — the destination of `src:dst`, `src` alone, `HEAD` as the current branch, `:dst` as a delete — or, with no refspec, from the branch's configured push destination. When it cannot determine a target — `--all`, `--branches`, `--mirror`, `--tags`, an option it does not know, shell expansion in the push, a directory change before a push that needs the current branch, a tag refspec, or no configured push destination — it MUST deny the call and name `git push origin <branch>` as the form to use. A `Bash` call with no `git push`, and any call while no `push:<glob>` is declared, MUST pass unchanged. Codex keeps its `manual` guard capability.

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

#### Scenario: Nothing is checked without a push scope
- **WHEN** `authorize:` declares a bare `push`, or no `push` at all, and a `Bash` call runs `git push origin HEAD:main`
- **THEN** the guard does not intercept it
