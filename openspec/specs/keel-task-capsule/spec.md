## Purpose

Define how Keel compiles a compact OpenSpec task and its referenced authority into one versioned, fingerprinted execution capsule consumed by context, gates, projection, and review.
## Requirements
### Requirement: Keel compiles compact tasks into a complete execution capsule
Keel MUST accept a compact v4 task source and compile it with versioned defaults and referenced OpenSpec authority into `keel-task-capsule/v1`. The capsule MUST be complete enough for the current agent to execute without guessing and MUST remain a disposable view of OpenSpec rather than a new source of truth. Where the repository declares standing authorization, the capsule MUST resolve the autonomy default from that declaration and MUST name it as the source.

#### Scenario: Normal implementation task inherits defaults
- **WHEN** a task declares resolvable `Covers`, concrete `Touch`, and `Verify` with a supported strategy and at least one `M<n>` check
- **THEN** the capsule supplies default implementation mode, current-agent ownership, base Read context, hard-stop autonomy, no coupling, read-only helper authority, standard prohibitions, and derived Acceptance
- **AND THEN** the source task is not required to repeat those defaults

#### Scenario: Repository-declared authorization replaces the hard-stop default
- **WHEN** a task declares no `Autonomy boundary:` and `keel/config.yaml` standing-authorizes an action
- **THEN** the capsule resolves that action as authorized in place of the hard-stop default
- **AND THEN** the capsule records the repository declaration as the source of that entry
- **AND THEN** every action the declaration does not name still resolves to hard-stop

#### Scenario: Non-default behavior is explicit
- **WHEN** a task needs diagnose-only, plan-first, coupling, additional Read paths, an authorized fallback, or a task-specific Acceptance delta
- **THEN** the source task declares only the applicable non-default clauses
- **AND THEN** the capsule includes their normalized executable meaning

#### Scenario: Incomplete capsule does not compile
- **WHEN** a required reference, field, conditional clause, or default cannot be resolved uniquely
- **THEN** compilation returns structured diagnostics without a usable capsule
- **AND THEN** no consumer substitutes guessed values

### Requirement: Task modes and conditional fields are executable
Keel MUST validate task mode and conditional fields as behavior, not unchecked labels. Where a diagnostic requires the author to add a field, it MUST name that field and its exact line prefix rather than describing the authority abstractly. A task whose whole effect is an authorized repository-level action and which writes no worktree file MUST have a legal mode of its own, rather than being forced to name a Touch path it does not write.

#### Scenario: Diagnose-only has no product Touch
- **WHEN** a task declares `Mode: diagnose-only` and `Touch: none`
- **THEN** the capsule accepts the contract and prohibits product writes
- **AND THEN** `task-start` does not reject the literal `none` as an unspecified placeholder

#### Scenario: Repo-action performs a repository action without worktree writes
- **WHEN** a task declares `Mode: repo-action` and `Touch: none`
- **THEN** the capsule accepts the contract, prohibits product writes, and is the one mode that does not prohibit committing, because performing that action is the task
- **AND THEN** the mode is recorded in the compiled capsule, so the authorization is visible in the fingerprint rather than inferred from an empty field

#### Scenario: Repo-action still refuses a product Touch
- **WHEN** a task declares `Mode: repo-action` with a concrete Touch path
- **THEN** compilation fails, naming the `Touch: none` the mode requires
- **AND THEN** an unsupported mode value is still rejected by a diagnostic listing every supported mode

#### Scenario: Implementation requires concrete Touch
- **WHEN** an implementation task has no concrete Touch path
- **THEN** compilation fails before task execution

#### Scenario: Coupling fields are conditional
- **WHEN** coupling is none
- **THEN** candidate-only coupling fields are absent or rejected as contradictory
- **AND WHEN** coupling is required
- **THEN** the capsule requires the design Coupled Iteration Contract and task candidate boundaries, stop rules, final assertions, and evidence contract

#### Scenario: Authority diagnostic names the field to add
- **WHEN** a task's `Covers` references an unresolved `Q<n>` and no authorized fallback is declared on the task
- **THEN** the `unresolved-authority` diagnostic names the `Autonomy boundary:` field and the `Pre-authorized fallback:` line prefix it requires
- **AND THEN** the diagnostic does not imply that prose in `design.md` satisfies the check

### Requirement: Covers resolves durable authority and Acceptance
Keel MUST resolve each `Covers` entry to a unique OpenSpec scenario or critical D/F/A statement and MUST derive the task's observable Acceptance from that authority plus any explicit task-specific delta. A reference whose first segment names an existing capability MUST NOT degrade into an unlinked free-text reference, whatever its segment count. When a candidate requirement or scenario name in the target capability itself contains the ` / ` hierarchy separator, the diagnostic MUST say so, because no spelling of the reference can resolve.

#### Scenario: Scenario reference derives Acceptance
- **WHEN** `Covers` uniquely names an OpenSpec scenario
- **THEN** the capsule includes that scenario's observable outcomes and source location
- **AND THEN** the task does not need to duplicate the same Acceptance text

#### Scenario: Critical expectation coverage is closed
- **WHEN** a relevant critical expectation affects the selected task
- **THEN** the capsule identifies its executable slice, durable deferral owner, or explicit discard rationale
- **AND THEN** compilation fails when none exists

#### Scenario: Ambiguous or missing reference fails
- **WHEN** a `Covers` reference is missing, duplicated, unresolved, or points to an unresolved Q<n> without authorized fallback
- **THEN** compilation fails with the offending reference and reason
- **AND THEN** Keel does not match a similar heading heuristically

#### Scenario: Separator collision is named
- **WHEN** a `Covers` reference cannot resolve and the target capability contains a requirement or scenario whose own name contains the ` / ` separator
- **THEN** the `unresolved-covers` diagnostic states that the name contains the separator and cannot be referenced
- **AND THEN** the author is not left to infer the cause from a reference that looks correct

#### Scenario: Over-segmented capability reference does not degrade silently
- **WHEN** a `Covers` reference carries more segments than the hierarchy allows and its first segment names a capability whose spec exists
- **THEN** it is reported as an unresolved reference rather than accepted as a free-text reference
- **AND THEN** a free-text reference whose first segment names no existing capability is still accepted unchanged

### Requirement: Verification strategy and evidence labels are connected
Every executable task capsule MUST contain one supported verification strategy and one or more unique, ordered `M<n>` checks that can prove the resolved Acceptance through a public interface or an explicitly authorized evidence alternative. A check MAY carry an optional `(fast)` or `(full)` verification-layer tag written immediately after its `M<n>` label; an untagged check is `full`. The tag is declarative metadata that records which checks belong to the fast inner loop and MUST NOT change red-green evidence rules or what `change-close` requires — every `M<n>` still needs its Evidence.

#### Scenario: Behavioral strategy requires behavioral proof
- **WHEN** a task uses vertical-tdd, regression-first, characterization, snapshot-characterization, or rendered-behavior
- **THEN** its checks and Evidence identify the behavior exercised and the public interface used
- **AND THEN** build-only, signature-only, collection-shape-only, or self-mocked evidence does not satisfy the capsule

#### Scenario: Red and green evidence use the same check
- **WHEN** the selected strategy requires red-green execution
- **THEN** Evidence records the applicable `M<n>.red` and `M<n>.green` outcomes for the same behavior check
- **AND THEN** the task cannot complete with green-only evidence unless an explicit, authorized characterization rationale applies

#### Scenario: Evidence-first is explicit
- **WHEN** a docs, configuration, diagnosis, or other non-behavioral task cannot use a meaningful red-green loop
- **THEN** the capsule uses `evidence-first`
- **AND THEN** its checks state the observable artifact or diagnosis evidence that proves Acceptance

#### Scenario: Checks may declare a verification layer
- **WHEN** a check is written with a `(fast)` or `(full)` tag after its `M<n>` label
- **THEN** the compiled capsule records that check's verification layer, and a check with no tag compiles as `full`
- **AND THEN** the tag does not alter the check text, its Evidence label mapping, or the red-green and change-close requirements

### Requirement: Keel fingerprints executable authority deterministically
Keel MUST compute a SHA-256 fingerprint over a canonical representation of the executable capsule authority and MUST produce the same value for semantically equivalent inputs across supported targets and operating systems.

#### Scenario: Mutable completion data does not drift the contract
- **WHEN** checkbox state, Evidence, Review, Report, comments, or presentation whitespace changes without changing executable authority
- **THEN** the capsule fingerprint remains unchanged

#### Scenario: Authority change drifts the contract
- **WHEN** resolved expectation text, mode, scope, Acceptance, verification, stop/autonomy, coupling, defaults version, or prohibitions change
- **THEN** the capsule fingerprint changes

#### Scenario: Ordering preserves semantics
- **WHEN** unordered source lists use a different presentation order
- **THEN** canonicalization produces the same fingerprint
- **AND WHEN** command or coupled-candidate order changes
- **THEN** canonicalization preserves that semantic difference

### Requirement: The durable task records its accepted fingerprint
`task-start` MUST return the compiled capsule and fingerprint without writing. The current agent MUST record the accepted fingerprint in durable task execution evidence before product implementation, and later continuation and completion MUST compare the recorded value to a fresh compilation.

#### Scenario: Fresh task records its anchor
- **WHEN** `task-start` passes for a selected task
- **THEN** the current agent records the returned capsule schema and fingerprint in the task before implementation
- **AND THEN** no Keel-owned session file or cache is created

#### Scenario: Resume reconstructs the same contract
- **WHEN** another turn, session, agent, or worktree resumes the selected task
- **THEN** Keel recompiles from current OpenSpec authority and compares it to the recorded fingerprint
- **AND THEN** matching authority permits the current agent to continue from durable Evidence and Git state

#### Scenario: Drift requires explicit reauthorization
- **WHEN** the fresh fingerprint differs from the recorded fingerprint
- **THEN** execution hard-stops before further implementation or completion
- **AND THEN** reauthorization requires returning to authoring, explaining the change, clearing stale execution evidence, and recording a newly passing start fingerprint

### Requirement: Expanded v3 tasks normalize through the same compiler
Keel v4 MUST accept compatible expanded v3 task fields through the same parser and compiler used for compact tasks. It MUST NOT maintain a separate legacy parser or emit expanded v3 tasks from the v4 template. When a task declares `Verify` but that field is judged non-concrete, Keel MUST report that judgment as its own diagnostic naming the matched placeholder token, and MUST NOT silently apply the expanded v3 required-field set instead. When a task declares neither `Verify` nor `Commands` it has declared no verification form at all, and Keel MUST report the missing verification declaration alone. The expanded v3 required-field set MUST be the compact set with `Commands` in place of `Verify`: Keel MUST NOT require a field whose value the compiler supplies from a documented default, whose value it derives from other authority, whose value it consumes nowhere, or that another check requires under the condition that needs it.

#### Scenario: Compatible expanded and compact tasks agree
- **WHEN** an expanded v3 task and compact v4 task express the same executable authority
- **THEN** they compile to equivalent capsule authority and the same fingerprint

#### Scenario: Expanded field contradicts a v4 rule
- **WHEN** an explicit legacy field conflicts with a mode rule, default, resolved scenario, verification strategy, or coupling contract
- **THEN** compilation fails with a migration diagnostic
- **AND THEN** Keel does not silently prefer either value

#### Scenario: Non-concrete Verify is reported, not silently downgraded
- **WHEN** a task declares `Verify` and the concreteness test judges it unfilled
- **THEN** the diagnostics name the matched token and state that compact detection requires a concrete `Verify`
- **AND THEN** the task is not reported as missing the expanded v3 fields it never declared

#### Scenario: A task declaring no verification form reports one problem
- **WHEN** a task declares neither `Verify` nor `Commands`
- **THEN** the diagnostics say that no verification form was declared and name `Verify` as the compact field to add
- **AND THEN** the diagnostics do not list the expanded v3 fields the task never declared

#### Scenario: A defaulted or derived field is not required
- **WHEN** an expanded v3 task omits a field whose value the compiler supplies from a documented default, derives from other authority, or consumes nowhere
- **THEN** the task is not reported as missing that field
- **AND THEN** a field owned by the coupling contract is reported only when `Coupling: required`

#### Scenario: Documented patterns in inline code are concrete
- **WHEN** a field's text carries unfilled-token forms only inside inline code spans, such as a filename pattern or prose naming the token forms themselves
- **THEN** the concreteness test judges the field filled
- **AND THEN** the same token form written outside inline code is still judged unfilled
- **AND THEN** a field whose entire text is one inline code span is not judged empty by the stripping

### Requirement: A regression check declares itself and is exempt from red-green

A red-green strategy proves a behavior by failing before the implementation and
passing after. A regression check makes the opposite claim — that something
already green is still green — and has no honest red. Requiring one of it leaves
an author two options, fabricating a red or folding the guard into the behavior
check, and both are worse than the check they replace: the first is the
dishonesty the evidence rule exists to prevent, and the second lets the gate's
shape decide how the task is decomposed.

An `M<n>` check MAY therefore carry a `(regression)` tag after its label. A
tagged check MUST still record concrete Evidence for its bare label; the
exemption is from `.red` and `.green`, not from proof. A task whose strategy is
red-green MUST retain at least one untagged check, so a strategy cannot be
emptied out by tagging every check in it.

The tag MUST be part of the compiled capsule, so the exemption is a declared
term of the contract that review and the fingerprint both see rather than a
silent skip. A check that carries no tag MUST compile exactly as it does today,
so no existing task's fingerprint moves.

#### Scenario: A regression guard stands as its own check

- **WHEN** a task under a red-green strategy declares a check tagged `(regression)` alongside an untagged behavior check
- **THEN** completion requires `.red` and `.green` only for the untagged check
- **AND THEN** the tagged check still fails completion if its bare-label Evidence is missing

#### Scenario: A red-green strategy cannot be emptied out

- **WHEN** every check in a task under a red-green strategy is tagged `(regression)`
- **THEN** the gate refuses the task and states that at least one check must carry the strategy
- **AND THEN** the diagnostic distinguishes this from missing evidence

#### Scenario: Untagged checks compile unchanged

- **WHEN** a task declares only untagged checks
- **THEN** its compiled capsule and fingerprint are identical to what the same task compiled before the tag existed
- **AND THEN** no already-recorded contract anchor is invalidated by this capability

#### Scenario: Red and green are additional to the bare label

- **WHEN** an author reads the tasks template for what a red-green strategy must record
- **THEN** it states that `.red` and `.green` entries accompany the bare `M<n>` Evidence rather than replacing it
- **AND THEN** an author following the template does not meet a missing-evidence refusal for the label itself

### Requirement: A Covers question reference is the subject of its entry
Keel MUST recognize an unresolved `Q<n>` reference only where it opens a `Covers` entry, so that naming a resolved question as supporting detail alongside the fact that closed it does not demand a pre-authorized fallback. Keel MUST NOT scan the whole `Covers` field for the identifier pattern.

#### Scenario: An open question is the subject of its entry
- **WHEN** a `Covers` entry opens with an unresolved `Q<n>` reference and the task declares no `Pre-authorized fallback:` line
- **THEN** `task-start` refuses the task and names that question

#### Scenario: A resolved question cited as supporting detail does not block
- **WHEN** a `Covers` entry opens with a fact reference and names a resolved `Q<n>` in its supporting text
- **THEN** the question is not treated as unresolved authority
- **AND THEN** the task is not required to declare a pre-authorized fallback for it

### Requirement: A non-concrete check names the token that made it non-concrete
Keel MUST name the matched unfilled-slot token when a `M<n>` check is judged non-concrete because of one, and MUST keep an unqualified diagnostic only when the check is empty or explicitly `none`/`pending`.

#### Scenario: An unfilled slot in a check is named
- **WHEN** a `M<n>` check carries an unfilled-slot token outside inline code
- **THEN** the diagnostic names that token
- **AND THEN** replacing the named token makes the same check concrete

#### Scenario: An empty check keeps the unqualified diagnostic
- **WHEN** a `M<n>` check is empty or explicitly `none` or `pending`
- **THEN** the diagnostic states that the check must define a concrete public check without naming a token

### Requirement: A task body ends at the next task or the next heading
Task parsing MUST end a task's body at the next task or at the next `##` heading, whichever comes first, so that a change-level section is never read as a field of the preceding task. Every consumer of a task's extent MUST use that same boundary rather than recomputing one.

#### Scenario: A change-level section is not the last task's Evidence
- **WHEN** a tasks file declares `## Invalidates` or `## Expectation Coverage` after its last task
- **THEN** that section's lines are not appended to any task field
- **AND THEN** an unfilled-slot token quoted inside the section does not make the last task's `Evidence` non-concrete

#### Scenario: A group heading is not the previous task's field
- **WHEN** a tasks file declares a task group heading between two tasks
- **THEN** that heading is not appended to the preceding task's last field

#### Scenario: A quoted invalidation phrase satisfies both checks
- **WHEN** an `## Invalidates` entry quotes stale wording that contains an unfilled-slot token
- **THEN** the double-quoted phrase satisfies the searchable-phrase check
- **AND THEN** the same text does not make any task's `Evidence` non-concrete

#### Scenario: The anchor search uses the task's own extent
- **WHEN** the `Contract` anchor of the last task is located for recording
- **THEN** the search covers only that task's body and does not reach a trailing section

