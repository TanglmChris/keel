## MODIFIED Requirements

### Requirement: Expanded v3 tasks normalize through the same compiler
Keel v4 MUST accept compatible expanded v3 task fields through the same parser and compiler used for compact tasks. It MUST NOT maintain a separate legacy parser or emit expanded v3 tasks from the v4 template. When a task declares `Verify` but that field is judged non-concrete, Keel MUST report that judgment as its own diagnostic naming the matched placeholder token, and MUST NOT silently apply the expanded v3 required-field set instead.

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

#### Scenario: Documented patterns in inline code are concrete
- **WHEN** a field's text carries unfilled-token forms only inside inline code spans, such as a filename pattern or prose naming the token forms themselves
- **THEN** the concreteness test judges the field filled
- **AND THEN** the same token form written outside inline code is still judged unfilled
- **AND THEN** a field whose entire text is one inline code span is not judged empty by the stripping

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

### Requirement: Task modes and conditional fields are executable
Keel MUST validate task mode and conditional fields as behavior, not unchecked labels. Where a diagnostic requires the author to add a field, it MUST name that field and its exact line prefix rather than describing the authority abstractly.

#### Scenario: Diagnose-only has no product Touch
- **WHEN** a task declares `Mode: diagnose-only` and `Touch: none`
- **THEN** the capsule accepts the contract and prohibits product writes
- **AND THEN** `task-start` does not reject the literal `none` as an unspecified placeholder

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
