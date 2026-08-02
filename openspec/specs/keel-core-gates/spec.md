## Purpose

Define Keel's shared deterministic task and change gates and their boundary with agent-owned semantic review.
## Requirements
### Requirement: Keel Core owns deterministic gate logic

Keel MUST implement task and change gate policy once in a shared Core. Target hooks, commands, and plugins MUST consume the Core result and MUST NOT maintain independent OpenSpec parsers or completion rules.

#### Scenario: Target automation calls shared Core
- **WHEN** a target-native hook invokes a Keel task or close gate
- **THEN** the hook consumes the shared Core result
- **AND THEN** the hook contains only target event mapping and result presentation or blocking behavior

#### Scenario: Manual execution uses the same gate
- **WHEN** a target lacks reliable native automation
- **THEN** the explicit Keel command runs the same Core gate used by automated adapters

### Requirement: Keel exposes three gate stages

Keel MUST expose `task-start`, `task-complete`, and `change-close` stages with explicit change/task selection or conservative unique inference.

#### Scenario: Task-start validates executable structure
- **WHEN** `task-start` evaluates a selected task
- **THEN** it checks Covers, Read, Touch, Acceptance, Commands, mode, Stop or Autonomy boundaries, and any required Coupled Iteration Contract
- **AND THEN** a structurally incomplete task does not pass

#### Scenario: Task-complete validates durable completion evidence
- **WHEN** `task-complete` evaluates a selected task or authorized contiguous task group
- **THEN** it checks every required command label has concrete Evidence
- **AND THEN** it checks Review status and blocker or finding ownership

#### Scenario: Change-close validates closure
- **WHEN** `change-close` evaluates sync or archive readiness
- **THEN** it checks expectation closure, task completion consistency, Review evidence, unresolved follow-up ownership, and action-specific prerequisites
- **AND THEN** missing closure does not pass

### Requirement: Semantic judgment remains agent-owned

Keel MUST NOT claim that deterministic gate structure proves product intent, behavioral test sufficiency, design quality, or risk completeness. Required semantic conclusions MUST be recorded by the current agent in task Review evidence. Wherever a durable follow-up owner is required, the accepted forms MUST include an external tracker reference alongside the repository-local forms.

#### Scenario: Completion Review is required
- **WHEN** a task is presented to `task-complete`
- **THEN** its Evidence contains Review `Status`, `Acceptance check`, `Scope check`, and `Findings`
- **AND THEN** a missing or non-passing required Review produces `needs-review`

#### Scenario: Findings require durable ownership
- **WHEN** Review identifies an unresolved finding
- **THEN** `task-complete` requires a durable OpenSpec task, new change, archive-evidence owner, absolute `http` or `https` tracker reference, or explicit discard rationale
- **AND THEN** `keel/HANDOFF.md` is not accepted as that owner

#### Scenario: An external tracker owns a finding without a local proxy file
- **WHEN** a Review `Findings` value or an `## Expectation Coverage` `Durable owner:` entry names an absolute `http` or `https` reference
- **THEN** the gate accepts it as a durable owner without requiring a repository-local file written only to satisfy the shape
- **AND THEN** both checks accept the tracker form, and every form either check accepted before is still accepted

#### Scenario: Gate does not reinterpret acceptance
- **WHEN** command Evidence and Review are present
- **THEN** Core validates their required shape and references
- **AND THEN** Core does not replace `keel-review-checklist` by independently judging whether the command proves Acceptance

### Requirement: Dirty-worktree attribution is conservative

Keel MUST NOT attribute dirty paths to a selected task unless a trustworthy comparison base exists. A base supplied by the caller is one; a dirty-path set Keel itself recorded when the task started is another, and `keel gate task-complete` MUST use that recorded set when the caller supplies no base, refusing a path that is dirty now, was not dirty when the task started, and lies outside the selected task's Touch. When no base is supplied and no set was recorded, scope attribution remains semantic review evidence, because an absent record is not a record that nothing was dirty. An explicitly supplied base MUST take precedence over the recorded set, since the two answer different questions and the caller asked the broader one.

A path that was already dirty when the task started is not attributed to that task even if the task modified it again, and the requirement text MUST say so, so a reader learns the limit from the specification rather than from a write that was never reported. The disposable guard manifest `keel/guard.json` — the one artifact the gate contract itself permits a gate to write — MUST NOT be attributed as an outside-Touch scope failure, and changed paths under the selected change's own `openspec/changes/<change>/` directory — the authoring artifacts the gate is completing against — MUST NOT be attributed as outside-Touch scope failures either. A changed path that a **completed** task of the same change declares in its own Touch MUST NOT be attributed to the selected task, and that exclusion MUST be reported rather than applied silently, because a base comparison cannot establish which task wrote a path. A renamed path reported by the worktree as a single `old -> new` entry MUST be attributed as its two independent endpoints, so a rename whose old and new paths are both in Touch is not a false outside-Touch failure.

#### Scenario: Dirty worktree without base or record needs review
- **WHEN** task completion runs in a dirty worktree with no explicit trustworthy base and no recorded task-start dirty set
- **THEN** Keel exposes the dirty state as a warning or `needs-review`
- **AND THEN** it does not fail solely because unrelated dirty paths exist
- **AND THEN** it does not claim those paths belong to the task

#### Scenario: A write outside Touch is refused without the caller asking
- **WHEN** a task records its dirty-path set at task start, a path outside its Touch becomes dirty afterwards, and task completion runs with no explicit base
- **THEN** completion fails naming that path as outside Touch
- **AND THEN** the refusal does not require the caller to have supplied a comparison base

#### Scenario: A path already dirty at task start is not attributed
- **WHEN** a path outside Touch was already dirty when the task started
- **THEN** completion does not attribute it to the selected task
- **AND THEN** the outcome is the same whether or not the task modified that path again

#### Scenario: An explicit base takes precedence over the recorded set
- **WHEN** task completion runs with an explicit trustworthy base and a recorded task-start dirty set both available
- **THEN** the comparison answers against the supplied base
- **AND THEN** a path changed since that base but already dirty at task start is still attributed

#### Scenario: The unattributed-dirty warning keeps naming its paths
- **WHEN** completion reports dirty paths it did not attribute to the selected task
- **THEN** it names those paths rather than only counting them
- **AND THEN** a rename's two endpoints both appear, so the warning remains usable as the only surface that shows what the worktree parser produced

#### Scenario: Explicit base enables path comparison
- **WHEN** the caller supplies a valid comparison base
- **THEN** Keel may compare changed paths to Touch
- **AND THEN** paths outside Touch produce a deterministic scope failure

#### Scenario: Nested paths match double-star Touch globs
- **WHEN** the caller supplies a valid comparison base and the task Touch list contains a `**` glob entry
- **THEN** changed paths nested arbitrarily deep under the glob's base directory are attributed inside Touch
- **AND THEN** the comparison does not report a false `outside-touch` scope failure for those paths

#### Scenario: The gate's own guard manifest is never outside Touch
- **WHEN** the caller supplies a valid comparison base and the disposable guard manifest `keel/guard.json` is present as a changed or dirty path
- **THEN** the comparison does not attribute the manifest as an outside-Touch scope failure and completion needs no prior `keel guard clear`
- **AND THEN** every other path outside Touch still produces a deterministic scope failure

#### Scenario: The selected change's authoring artifacts are never outside Touch
- **WHEN** the caller supplies a valid comparison base and changed paths exist under the selected change's own `openspec/changes/<change>/` directory
- **THEN** the comparison does not attribute those authoring artifacts as outside-Touch scope failures
- **AND THEN** paths under other changes' directories, the archive tree, `openspec/specs/`, and `openspec/schemas/` still produce deterministic scope failures when outside Touch

#### Scenario: A completed task's uncommitted work is not the next task's scope failure
- **WHEN** the caller supplies a valid comparison base and a changed path outside the selected task's Touch is declared in the Touch of another task of the same change that is checked complete
- **THEN** the comparison does not attribute that path to the selected task
- **AND THEN** it reports the exclusion, naming the path and the completed task that declares it, because a base comparison cannot establish which task wrote the path

#### Scenario: An unfinished task's Touch grants nothing
- **WHEN** a changed path outside the selected task's Touch is declared only by a task of the same change that is not checked complete, or by no task at all
- **THEN** the path still produces a deterministic `outside-touch` scope failure
- **AND THEN** a task whose Touch is `none` contributes no path claims

#### Scenario: A rename within Touch attributes to both endpoints
- **WHEN** the caller supplies a valid comparison base and a tracked file is renamed so the worktree reports one `old -> new` entry whose old and new paths are both listed in Touch
- **THEN** the comparison attributes the old and new paths independently, each inside Touch
- **AND THEN** it does not report a false `outside-touch` scope failure for the combined rename entry

#### Scenario: Keel stores no baseline
- **WHEN** `task-start` completes
- **THEN** Keel does not persist a diff snapshot, hash set, or execution baseline for later completion

### Requirement: All gate stages consume one normalized task contract
Keel Core MUST parse and compile a selected task once through the shared task-capsule module. `context`, `task-start`, `task-complete`, `change-close`, projection, adapters, and validators MUST consume that normalized result and MUST NOT derive independent field defaults or task completion rules.

#### Scenario: Parser behavior is shared
- **WHEN** the same task is evaluated by context, a gate, or a target projection
- **THEN** every consumer receives the same capsule schema, diagnostics, resolved authority, and fingerprint
- **AND THEN** a fixture cannot pass one consumer because another consumer reparsed the Markdown differently

#### Scenario: Invalid contract blocks every consumer
- **WHEN** capsule compilation returns a structural diagnostic
- **THEN** `task-start` fails and projection is blocked
- **AND THEN** context reports the task as blocked rather than presenting a partially executable next action

### Requirement: Task-start validates executable semantics and labels
`task-start` MUST validate supported mode values, mode-specific Touch behavior, resolvable Covers authority, verification strategy, unique contiguous `M<n>` labels, command-to-evidence expectations, stop/autonomy boundaries, and conditional coupling fields.

#### Scenario: Unsupported mode fails
- **WHEN** a selected task declares a mode outside implementation, diagnose-only, or plan-first
- **THEN** `task-start` fails with the invalid value and supported set

#### Scenario: Command labels are malformed or disconnected
- **WHEN** verification labels are duplicated, non-contiguous, not `M<n>`, missing a check, or cannot map to required evidence
- **THEN** `task-start` fails before implementation

#### Scenario: Diagnose-only none is valid
- **WHEN** a diagnose-only task compiles with `Touch: none`
- **THEN** `task-start` accepts the no-write scope
- **AND THEN** its capsule prohibits product writes

### Requirement: Gate results expose capsule and fingerprint evidence

The versioned machine-readable `task-start` result MUST include the capsule schema, normalized capsule, fingerprint, and diagnostics needed for the current agent to record a durable start anchor. When the caller explicitly passes `--record`, a passing `task-start` MUST write that anchor itself by replacing the selected task's `- Contract:` Evidence line with the compiled fingerprint line, whatever value that line currently holds, and MUST refuse deterministically — writing nothing — only when the selected task has no `- Contract:` line at all. The result MUST report which outcome occurred, and a re-record that replaces a different recorded fingerprint MUST warn that execution evidence produced under the previous contract is stale. Later task gates MUST report recorded-versus-current fingerprint status.

#### Scenario: Passing start exposes recording data
- **WHEN** `task-start` passes
- **THEN** its JSON includes `keel-task-capsule/v1`, the fingerprint algorithm and value, and the complete normalized contract
- **AND THEN** human-readable output identifies the fingerprint without dumping unnecessary capsule detail

#### Scenario: Explicit record replaces only the Contract anchor
- **WHEN** `task-start` passes with `--record` and the selected task's Evidence contains the line `- Contract: pending`
- **THEN** the gate replaces exactly that line with the compiled `keel-task-capsule/v1` fingerprint line consumed by the existing anchor read path, and reports the outcome as `recorded`
- **AND THEN** no other line of `tasks.md` changes, and the recompiled fingerprint is unchanged so any active guard stays valid

#### Scenario: Reauthorization replaces a recorded anchor and warns
- **WHEN** `--record` is passed and the selected task's `- Contract:` line already carries a fingerprint that differs from the freshly compiled one
- **THEN** the gate replaces that line with the new fingerprint line, reports the outcome as `rerecorded`, and carries the replaced value in the result
- **AND THEN** it warns that the previous contract's execution evidence is stale, naming the previous fingerprint, and no other line of `tasks.md` changes

#### Scenario: Re-recording an unchanged contract writes nothing
- **WHEN** `--record` is passed and the selected task's `- Contract:` line already carries exactly the freshly compiled fingerprint line
- **THEN** the gate reports the outcome as `unchanged` and leaves `tasks.md` byte-identical
- **AND THEN** it emits no stale-evidence warning, because the contract did not move

#### Scenario: Record without a Contract anchor refuses
- **WHEN** `--record` is passed but the selected task has no `- Contract:` Evidence line to anchor
- **THEN** `task-start` fails with a deterministic record refusal naming the missing anchor line and the literal form to add
- **AND THEN** it writes nothing, not even the guard manifest, and behavior without `--record` remains byte-identical to the pre-flag gate

#### Scenario: Completion sees contract drift
- **WHEN** the recorded start fingerprint differs from fresh compilation
- **THEN** `task-complete` fails with both values and the authority areas that changed when they can be determined deterministically
- **AND THEN** it does not accept otherwise complete Evidence

#### Scenario: Gates remain read-only
- **WHEN** a gate returns a capsule, fingerprint, or drift result
- **THEN** it stays read-only toward task authority: it does not clear evidence, repair the task, or accept new authority, and it does not write the start anchor unless the caller explicitly passed `--record`
- **AND THEN** the disposable guard manifest and the explicit `--record` anchor replacement, each written only by a passing `task-start`, are the only artifacts any gate may write

### Requirement: Completion evidence follows verification strategy
`task-complete` MUST validate that every required `M<n>` label has concrete strategy-appropriate Evidence and that the existing semantic Review covers the resolved Acceptance and Touch scope.

#### Scenario: TDD evidence is incomplete
- **WHEN** a red-green strategy requires `M1.red` and `M1.green` but one is absent, pending, or non-concrete
- **THEN** `task-complete` does not pass

#### Scenario: Evidence-first task is complete
- **WHEN** every evidence-first check has concrete observable evidence and semantic Review is pass
- **THEN** structural completion may pass without invented red-green records

### Requirement: Goal execution consumes gates without extending them
Native goal execution MUST consume the shared read-only `task-start` and `task-complete` results and MUST NOT add target-specific task parsers, writable gates, or evaluator-owned completion rules.

#### Scenario: Goal is prepared from task-start
- **WHEN** the current agent requests a goal projection for one task
- **THEN** Core returns the same capsule and fingerprint used by normal `task-start`
- **AND THEN** the target adapter performs no independent Markdown parsing

#### Scenario: Completion evidence is surfaced
- **WHEN** `task-complete` passes for the selected task
- **THEN** the current agent may surface its versioned status and selected fingerprint to the native evaluator
- **AND THEN** the gate still performs no task checkbox, goal, Review, or Evidence write

#### Scenario: Native evaluator disagrees with gate state
- **WHEN** the native evaluator's completion judgment conflicts with Core gate state
- **THEN** Core gate state and current-agent Review control Keel completion
- **AND THEN** the disagreement is reported as native projection evidence

### Requirement: Gate execution is deterministic and write-bounded

Core gates MUST run locally without network access or model calls. The only permitted project writes are the disposable `keel-write-guard/v1` manifest written by a passing `task-start` on the Claude target when `--no-guard` is absent, and the single-line replacement of the selected task's `- Contract:` Evidence anchor performed by a passing `task-start` when the caller explicitly passes `--record` and the anchor does not already hold the compiled fingerprint line. `task-complete`, `change-close`, and every failing or `needs-review` outcome MUST NOT write project state. Gates MUST return `pass`, `fail`, or `needs-review` through one versioned machine-readable result.

#### Scenario: Passing gate is process success
- **WHEN** every deterministic requirement for a gate is satisfied
- **THEN** gate status is `pass`
- **AND THEN** the command exits successfully

#### Scenario: Policy non-pass is distinguishable
- **WHEN** a gate detects a contract failure or required semantic review is absent
- **THEN** status is `fail` or `needs-review`
- **AND THEN** the process result is nonzero and distinguishable from an operational error

#### Scenario: Gate does not mutate evidence
- **WHEN** a gate evaluates task or change state
- **THEN** it does not mark tasks complete, write Review evidence, update HANDOFF, or repair artifacts
- **AND THEN** the guard manifest and the explicit `--record` Contract-anchor replacement, each written only by a passing `task-start`, are the sole exceptions to gate write-freedom

### Requirement: Accepted Review Status vocabulary is single-sourced and includes `done`

Keel MUST define the accepted Review `Status` vocabulary once as a single shared
constant consumed by both the completion gate and the context "already reviewed"
probe, and that vocabulary MUST include `done` alongside the existing passing
tokens. The two consumers MUST NOT maintain independent copies of the accepted
set.

#### Scenario: Gate and context share one accepted set

- **WHEN** the completion gate and the context already-reviewed probe each evaluate a Review `Status`
- **THEN** both derive the accepted set from the same shared constant
- **AND THEN** a `Status` token accepted by one is accepted by the other

#### Scenario: `done` completes on the Status axis

- **WHEN** a task presented to `task-complete` records Review `Status: done` with otherwise complete evidence
- **THEN** the gate treats the Review as passing on the Status axis
- **AND THEN** completion is not blocked solely because the token is `done` rather than `pass`

### Requirement: Gate rejections for validated forms name the field and accepted forms

When a completion or close gate rejects a hard-validated form — the Review
`Status` vocabulary, the Findings ownership shape, or the `## Expectation
Coverage` section — the resulting error MUST name the failing field or section
and MUST show the accepted forms or a minimal format sample, so an author can
repair from the message without reading validator source.

#### Scenario: Status rejection names the field and lists accepted tokens

- **WHEN** `task-complete` produces `semantic-review` because the Review `Status` is outside the accepted set
- **THEN** the error names the `Status` field and lists the accepted tokens, including `done`

#### Scenario: Findings rejection shows the accepted ownership forms

- **WHEN** `task-complete` produces `finding-owner` because a non-`none` Findings value has no durable owner
- **THEN** the error names the `Findings` field and shows the accepted forms: a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/<change>/…` artifact, any other repo-relative path that exists, or an absolute `http`/`https` tracker reference
- **AND THEN** the error states that `keel/HANDOFF.md` is not an accepted owner

#### Scenario: Expectation Coverage rejection carries a format sample

- **WHEN** `change-close` produces `expectation-coverage` because the section is missing or declares no `E<n>` closure
- **THEN** the error names the `## Expectation Coverage` section and carries a minimal `- E<n>: … Covered by: <task ids>` format sample
### Requirement: The tasks template emits a record-compatible Contract anchor

The shipped `keel-spec-driven` tasks template MUST emit the Contract evidence
anchor as the literal line `- Contract: pending`, so that `keel gate task-start
--record` can anchor a freshly-scaffolded task without manual editing. Validation
MUST enforce that the template's anchor stays in this record-compatible form.

#### Scenario: Fresh scaffold is record-able

- **WHEN** a task is scaffolded from the shipped tasks template and `task-start` passes with `--record`
- **THEN** the gate finds the literal `- Contract: pending` anchor and replaces it with the compiled fingerprint line
- **AND THEN** no manual editing of the anchor is required first

#### Scenario: Template anchor form is validated

- **WHEN** validation inspects the shipped tasks template
- **THEN** it requires the Contract anchor to be the literal `- Contract: pending`
- **AND THEN** it does not require a descriptive suffix that the `--record` matcher would reject

### Requirement: A contract anchor is reverifiable while its change is live

A recorded fingerprint is described as recompiled and compared at resume,
projection, and completion. That guarantee holds while the change is live and
stops holding when it is archived: the compiled capsule records each authority's
`source` as a path under the change directory, and archiving renames that
directory, so an archived task recompiles to a different value. Nothing is
broken by this — an archived task is never resumed or completed — but an
unstated boundary reads as no boundary, and a reader who recompiles an archived
anchor to check it will conclude the contract drifted.

Keel MUST state that a contract anchor is reverifiable for as long as its change
is live, and becomes a historical record once the change is archived. Keel MUST
NOT claim or imply that an archived anchor can be recompiled to the value it
records.

#### Scenario: A live anchor recompiles to its recorded value

- **WHEN** a task of an active change is recompiled at resume, projection, or completion
- **THEN** its fingerprint equals the value recorded in its Evidence `Contract` line unless the contract genuinely changed
- **AND THEN** a difference is contract drift and hard-stops

#### Scenario: An archived anchor is a record, not an assertion

- **WHEN** a task under `openspec/changes/archive/` is recompiled
- **THEN** the difference from its recorded anchor is expected, because the change directory it names has been renamed
- **AND THEN** the documented guarantee does not claim otherwise, so the difference is not read as drift

### Requirement: task-complete infers only a task that has started
When no task is named explicitly, `task-complete` MUST NOT infer a task whose Evidence `Contract` anchor holds no compiled fingerprint. It MUST refuse with a selection diagnostic that names the task it would have inferred, the most recently checked task, and the explicit selection flag. `task-start` MUST keep the first-unchecked default, because a task that has not started is the task it selects.

#### Scenario: The inferred task has never started
- **WHEN** `task-complete` runs without an explicit task and the first unchecked task records no fingerprint in its Evidence `Contract` anchor
- **THEN** the gate refuses on selection rather than reporting that task's readiness problems
- **AND THEN** the diagnostic names the inferred task, the most recently checked task, and the explicit selection flag

#### Scenario: The inferred task has recorded its start fingerprint
- **WHEN** `task-complete` runs without an explicit task and the first unchecked task records a compiled fingerprint in its Evidence `Contract` anchor
- **THEN** the gate evaluates that task's completion evidence as before

#### Scenario: An explicitly named task is never second-guessed
- **WHEN** `task-complete` runs with an explicit task selection
- **THEN** the selection diagnostic does not apply and the named task is evaluated

### Requirement: Completion requires a recorded start fingerprint
`task-complete` MUST refuse a task whose Evidence `Contract` anchor holds no compiled fingerprint, whether that task was named explicitly or inferred, and MUST name the command that records one. A task that recorded no anchor has no drift detection, so completion MUST NOT report it as gated. `task-start` MUST NOT require an anchor, because it runs before one can exist.

#### Scenario: A named task with no recorded anchor is refused
- **WHEN** `task-complete` evaluates an explicitly named task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the gate does not pass
- **AND THEN** the diagnostic names the anchor and the command that records it

#### Scenario: A recorded anchor is compared, not counted
- **WHEN** `task-complete` evaluates a task whose `Contract` anchor holds a compiled fingerprint
- **THEN** the anchor is compared against the recompiled fingerprint, and a difference fails the gate
- **AND THEN** the presence of a well-formed digest is not by itself sufficient to satisfy the anchor requirement

#### Scenario: task-start does not require an anchor
- **WHEN** `task-start` evaluates a task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the missing anchor is not reported as a problem

### Requirement: A recorded anchor is compared against the recompiled fingerprint

`task-complete` MUST recompile the selected task's capsule and compare the result with the fingerprint recorded in its Evidence `Contract` anchor. A difference MUST fail the gate. It MUST NOT be reported as a warning or as `needs-review`, because drift returns the task to authoring rather than to the judgment of the agent recording its own Review.

The diagnostic MUST name the recorded value, the recompiled value, and the command that reauthorizes the task, and MUST state that execution evidence produced under the previous contract is stale.

Keel MUST NOT require the anchor to carry a capsule schema prefix. A fingerprint is a digest over the canonical capsule serialization, so a value that matches could only have come from the schema that produced it; the prefix is diagnostic detail, not a gate condition.

#### Scenario: A contract edited after recording is refused
- **WHEN** a task's Touch, Verify, Covers, or a boundary is changed after its anchor was recorded, and `task-complete` evaluates it
- **THEN** the gate fails with a contract-drift diagnostic
- **AND THEN** the diagnostic names both the recorded and the recompiled fingerprint, names the reauthorization command, and states that evidence recorded under the previous contract is stale

#### Scenario: An anchor holding a foreign fingerprint is refused
- **WHEN** the recorded anchor is a well-formed digest that the task's own capsule does not compile to
- **THEN** the gate fails rather than accepting the anchor on its shape
- **AND THEN** a value of sixty-four zeros is refused for the same reason as any other non-matching value

#### Scenario: A matching anchor completes
- **WHEN** the recorded anchor equals the recompiled fingerprint
- **THEN** the comparison contributes no problem and the task's other completion evidence is evaluated as usual

#### Scenario: A schema prefix is not required
- **WHEN** the anchor records a bare `sha256:` digest with no capsule schema prefix, and that digest matches
- **THEN** the gate does not refuse it for the missing prefix

### Requirement: change-close compares the anchor of every checked task

`change-close` MUST compare each checked task's recorded anchor against its recompiled fingerprint, and MUST fail on a difference. A checked task that records no anchor MUST also fail, because an absent record and a drifted one are the same absence of proof at the gate that closes a live change.

The close diagnostic MUST identify the task and MUST NOT direct the reader to complete a task that is already checked.

#### Scenario: Drift introduced after completion is caught at the close
- **WHEN** every task is checked, a task's contract is then edited without reauthorizing, and `change-close` runs
- **THEN** the gate fails and names the task whose anchor no longer matches

#### Scenario: A checked task with no anchor fails the close
- **WHEN** a checked task's Evidence `Contract` anchor holds no compiled fingerprint and `change-close` runs
- **THEN** the gate fails rather than closing a change whose completion cannot be verified
- **AND THEN** the diagnostic does not tell the reader to complete a task that is already complete

#### Scenario: An unchanged change closes as before
- **WHEN** every checked task's anchor matches its recompiled fingerprint
- **THEN** the anchor comparison contributes no problem


### Requirement: Git path output is read in a form that carries no escaping

Keel MUST read changed and dirty paths from Git in NUL-separated form, so that no path it compares against Touch has been quoted or escaped. Keel MUST NOT rewrite backslashes in Git path output: Git emits forward slashes on every platform, and rewriting them corrupts any escape sequence that reaches the reader.

A path a task declares in Touch MUST be attributed to Touch whatever characters it contains, including non-ASCII characters, spaces, quotes, and backslashes.

#### Scenario: A non-ASCII path in Touch is not an outside-Touch failure
- **WHEN** a task declares a path containing non-ASCII characters in Touch and that file is the only change
- **THEN** `task-complete` attributes it inside Touch
- **AND THEN** no `outside-touch` problem names an escaped or partially decoded form of the path

#### Scenario: Spaces and quotes survive the read
- **WHEN** changed paths contain spaces, double quotes, or backslashes
- **THEN** each is compared against Touch as the filesystem spells it
- **AND THEN** the comparison does not depend on which Git subcommand reported the path

#### Scenario: A rename reports both endpoints undamaged
- **WHEN** a rename is reported whose endpoints contain characters Git would otherwise escape
- **THEN** both endpoints are attributed independently
- **AND THEN** neither endpoint is dropped or merged into the other

### Requirement: A finding resolved in its own task is recorded as resolved

`keel gate task-complete` MUST require a durable owner only for a finding that is still unresolved, which is what this capability and `keel-review-checklist` already state. A finding that was found and fixed inside the task recording it MUST have an accepted form of its own, so that no author has to record a repair as a discard in order to pass the gate.

The resolved disposition MUST carry evidence. Keel MUST accept an `M<n>` check label of the same task, or a repo-relative path that exists, and MUST NOT accept the marker alone — a disposition that asserts its own conclusion is weaker than the two it joins. Keel MUST NOT accept an `http` or `https` reference as evidence of resolution, because an external tracker means the work is owned elsewhere, which is the durable-owner state.

Every form accepted before this requirement MUST still be accepted, and `keel/HANDOFF.md` MUST still be refused in all of them.

#### Scenario: A finding fixed in the task passes without a discard reason
- **WHEN** Review `Findings` records a finding as resolved in this task and names an `M<n>` check of the same task as the evidence
- **THEN** `task-complete` accepts it without requiring a durable owner or a discard reason
- **AND THEN** the same text with no evidence named is refused

#### Scenario: Resolution evidence may be a path that exists
- **WHEN** a resolved finding names a repo-relative path as its evidence
- **THEN** the gate accepts it when that path exists and refuses it by name when it does not
- **AND THEN** an `http` or `https` reference is refused as resolution evidence while remaining accepted as a durable owner

#### Scenario: The accepted-forms diagnostic names all three dispositions
- **WHEN** `task-complete` produces `finding-owner` for a Findings value carrying no recognized disposition
- **THEN** the message names the resolved-here form and its evidence requirement alongside the durable-owner and discard forms
- **AND THEN** it still directs a path to be named after `Durable owner:` so it reads as the owner rather than a file the finding mentions

### Requirement: Two tasks shaped like one behavior are named at task-start

`keel gate task-start` MUST warn when another task in the same change declares an identical Touch set and the selected task's strategy is red-green, naming the other task so the author compares two things rather than being told something is wrong.

Keel MUST NOT fail or return `needs-review` for this shape. A genuine vertical split can share files, the judgment is semantic, and there is no mechanism to acknowledge a `needs-review` — turning a signal into a verdict would leave a legitimate split unstartable. The warning MUST NOT change the gate's status or exit code.

`keel-review-checklist` MUST ask the same question at completion, when the evidence that settles it exists.

#### Scenario: An identical Touch set under a red-green strategy is named
- **WHEN** `task-start` selects a task whose Touch set matches another task in the same change and whose strategy is red-green
- **THEN** the result carries a warning naming the other task
- **AND THEN** the status is unchanged and the exit code is unchanged, so the task starts normally

#### Scenario: A differing Touch set or a non-red-green strategy is silent
- **WHEN** no other task in the change declares the same Touch set, or the selected task's strategy is not red-green
- **THEN** no warning about task shape is produced
