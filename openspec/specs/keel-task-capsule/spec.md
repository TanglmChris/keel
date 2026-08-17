## Purpose

Define how Keel compiles a compact OpenSpec task and its referenced authority into one versioned, fingerprinted execution capsule consumed by context, gates, projection, and review.
## Requirements
### Requirement: Keel compiles compact tasks into a complete execution capsule

Keel MUST accept a compact v4 task source and compile it with versioned defaults and referenced OpenSpec authority into `keel-task-capsule/v1`. The capsule MUST be complete enough for the current agent to execute without guessing and MUST remain a disposable view of OpenSpec rather than a new source of truth. Where the repository declares standing authorization, the capsule MUST resolve the autonomy default from that declaration and MUST name it as the source. Where the repository declares delegation, the capsule MUST resolve the delegation default the same way and MUST name it as the source.

#### Scenario: Normal implementation task inherits defaults
- **WHEN** a task declares resolvable `Covers`, concrete `Touch`, and `Verify` with a supported strategy and at least one `M<n>` check
- **THEN** the capsule supplies default implementation mode, current-agent ownership, base Read context, hard-stop autonomy, no coupling, read-only helper authority, no delegation, standard prohibitions, and derived Acceptance
- **AND THEN** the source task is not required to repeat those defaults

#### Scenario: Repository-declared authorization replaces the hard-stop default
- **WHEN** a task declares no `Autonomy boundary:` and `keel/config.yaml` standing-authorizes an action
- **THEN** the capsule resolves that action as authorized in place of the hard-stop default
- **AND THEN** the capsule records the repository declaration as the source of that entry
- **AND THEN** every action the declaration does not name still resolves to hard-stop

#### Scenario: Repository-declared delegation replaces the no-delegation default
- **WHEN** a task declares no delegation entry and `keel/config.yaml` declares `delegation:`
- **THEN** the capsule resolves the declared tier in place of the no-delegation default
- **AND THEN** the capsule records `keel/config.yaml` as the source of that entry
- **AND THEN** read-only helper authority is unchanged, because a delegate and a helper are distinct roles

#### Scenario: A task's own delegation entry is not overridden
- **WHEN** a task authors a delegation entry and `keel/config.yaml` declares a different one
- **THEN** the capsule carries the task's entry unchanged and names the task as its source
- **AND THEN** the repository declaration supplies nothing for that task

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

### Requirement: An unresolved reference into an existing capability names what failed
When a `Covers` reference does not resolve, Keel MUST report which segment failed rather than the reference alone. When the reference's second segment names no Requirement but does name a Scenario the capability declares, the diagnostic MUST name the Requirement that Scenario belongs to and MUST state the corrected `capability / requirement / scenario` reference. When the capability declares no spec at all, the diagnostic MUST say so rather than describing the name inside it. Reporting what a spec contains is not heuristic matching: the reference still fails, with the same diagnostic code, and Keel MUST NOT resolve it to a near match.

#### Scenario: A Scenario offered as a Requirement is named as one
- **WHEN** a `Covers` reference's second segment names a Scenario the capability declares rather than a Requirement
- **THEN** the `unresolved-covers` diagnostic names the Requirement that Scenario sits under and states the corrected three-segment reference
- **AND THEN** the reference is still refused

#### Scenario: A name the spec does not declare is reported as read
- **WHEN** a `Covers` reference names an existing capability whose spec declares neither that Requirement nor a Scenario by that name
- **THEN** the diagnostic states that the capability's spec was read and holds no such name, and states the hierarchy
- **AND THEN** the reference is still refused

#### Scenario: A capability with no spec is distinguished from a name that is absent
- **WHEN** a `Covers` reference's first segment names a capability for which no spec exists
- **THEN** the diagnostic states that no spec declares that capability
- **AND THEN** it does not describe the remaining segments as the cause

#### Scenario: A Scenario declared under more than one Requirement offers no correction
- **WHEN** the named Scenario appears under more than one Requirement of the capability
- **THEN** the diagnostic names the Requirements it appears under
- **AND THEN** it states no single corrected reference

#### Scenario: What resolves is unchanged
- **WHEN** a `Covers` reference resolves to a Requirement or Scenario
- **THEN** it compiles to the same authority, source, and Acceptance as before
- **AND THEN** no diagnostic is added to a reference that resolves

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

### Requirement: A critical-statement Covers entry may carry a trailing annotation
Keel MUST resolve a `Covers` entry that opens with a `D<n>`/`F<n>`/`A<n>`/`Q<n>` identifier followed by a dash and trailing text as a reference to that critical statement, and MUST NOT degrade it into an unlinked free-text reference. The annotation is not authority: the statement text still comes from `design.md`, and the annotation is not compared against it. An identifier followed by anything other than whitespace or an em dash — `D2-compatible`, `D2:` — is not such an entry, and colon-form and free-text references are unchanged.

#### Scenario: An annotated critical-statement entry resolves as the statement
- **WHEN** a task's Covers entry reads `D2 — an annotation` and `design.md` carries D2 in an accepted shape
- **THEN** `keel gate task-start` resolves the entry as critical-statement authority for D2 with the `design.md` statement text

#### Scenario: An annotated entry whose identifier is absent fails loudly
- **WHEN** a task's Covers entry reads `D2 — an annotation` and D2 does not appear in the change's `design.md`
- **THEN** `keel gate task-start` fails the reference as missing rather than passing it as an unlinked free-text reference

#### Scenario: Colon-form and hyphenated free text stay free text
- **WHEN** a task's Covers entry reads `E1: observable behavior` or opens with text like `D2-compatible`
- **THEN** the entry resolves exactly as it did before this requirement, without becoming a critical-statement reference

### Requirement: A non-concrete check names the token that made it non-concrete
Keel MUST name the matched unfilled-slot token when a `M<n>` check is judged non-concrete because of one, and MUST keep an unqualified diagnostic only when the check is empty or explicitly `none`/`pending`.

#### Scenario: An unfilled slot in a check is named
- **WHEN** a `M<n>` check carries an unfilled-slot token outside inline code
- **THEN** the diagnostic names that token
- **AND THEN** replacing the named token makes the same check concrete

#### Scenario: An empty check keeps the unqualified diagnostic
- **WHEN** a `M<n>` check is empty or explicitly `none` or `pending`
- **THEN** the diagnostic states that the check must define a concrete public check without naming a token

### Requirement: A non-concrete required field names the token that made it non-concrete

Keel MUST name the matched unfilled-slot token when a required task field — `Covers`, `Verify`, `Evidence`, or the expanded v3 `Commands` — is judged non-concrete because of one, and MUST state that the token may be fenced in inline code when it is literal text rather than an unfilled slot. Keel MUST keep the unqualified diagnostic only when the field is empty or explicitly `none`/`pending`, where there is no token to name.

This is the same rule already required of a non-concrete `M<n>` check, and the diagnostics MUST NOT be phrased as two different events.

Naming the token MUST NOT change the verdict or the reported diagnostic code. A field carrying an unfilled token is not concrete both before and after; only the explanation changes.

#### Scenario: An unfilled slot in a required field is named
- **WHEN** a required task field carries an unfilled-slot token outside inline code
- **THEN** the diagnostic names the matched token
- **AND THEN** the diagnostic states that the token may be fenced in inline code when it is literal text
- **AND THEN** the field is still reported as not concrete

#### Scenario: An empty required field keeps the unqualified diagnostic
- **WHEN** a required task field is empty or explicitly `none` or `pending`
- **THEN** the diagnostic states that the field must be concrete without naming a token

#### Scenario: A prose token is reported rather than tolerated
- **WHEN** a required field carries an unfilled-token form inside ordinary prose, such as a numeric range written with bare angle brackets
- **THEN** the field is judged non-concrete and the matched span is named
- **AND THEN** the accepted repair is to reword or to fence the text, not a widened token pattern

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

### Requirement: A change-level section ends at the next heading or the next task
A change-level section of tasks.md — `## Invalidates`, `## Expectation Coverage` — MUST end at the next `##` heading or at the next task, whichever comes first. A tasks file's dominant structure is a list, so a section bounded only by the next heading extends over the task list whenever it is not the file's last section. The task half of this bound MUST be the task list already parsed for the same file, so that it cannot drift from the boundary applied to a task's own body, and both change-level sections MUST be bounded by one shared computation rather than by two that agree today.

The position of a change-level section MUST NOT affect any verdict. Keel MUST NOT require a section to sit in the file's tail, and MUST report the same problems for the same section content wherever the author placed it.

A line inside a task body MUST NOT close, satisfy, or contribute an entry to a change-level section. In particular a task field entry of `none` MUST NOT be read as the section's `- None.`, and an `E<n>` or `I<n>` line a task declares under its `Covers` MUST NOT be read as a section entry.

#### Scenario: A section above the task list is read as written
- **WHEN** `## Expectation Coverage` sits above the task list and every entry it declares is closed
- **THEN** `change-close` returns the same verdict it returns for the identical section in the file's tail
- **AND THEN** no problem names an entry that the section closes

#### Scenario: A task's own Covers entries are not section entries
- **WHEN** `## Expectation Coverage` sits above a task that declares `- E<n>:` lines under its `Covers`
- **THEN** those lines are not judged as coverage entries
- **AND THEN** no problem reports an `E<n>` that the section closes as lacking a closure

#### Scenario: An entry a task body appeared to close is still refused
- **WHEN** a change-level section sits above the task list, declares an entry with no closure, and a task body carries a field entry of `none`
- **THEN** the gate refuses the entry and names it
- **AND THEN** the section is not treated as having declared `- None.`

#### Scenario: Both change-level sections share the boundary
- **WHEN** `## Invalidates` sits above the task list
- **THEN** `task-start` reads only that section's own entries
- **AND THEN** it reports the same problems it reports for the identical section in the file's tail

#### Scenario: The tail position is unchanged
- **WHEN** a change-level section is the file's last section
- **THEN** every verdict, problem code, and message is what it was before the boundary gained its task half
