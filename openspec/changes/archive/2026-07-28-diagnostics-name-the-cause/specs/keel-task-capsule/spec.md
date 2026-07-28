## MODIFIED Requirements

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

## ADDED Requirements

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
