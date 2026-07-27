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
Keel MUST resolve every `Covers` reference to durable authority and derive the task's Acceptance from it. An unresolvable reference MUST fail with a diagnostic that identifies the unresolved reference. A reference whose first segment names an existing capability MUST NOT degrade into an unlinked free-text reference, whatever its segment count. When a candidate requirement or scenario name in the target capability itself contains the ` / ` hierarchy separator, the diagnostic MUST say so, because no spelling of the reference can resolve.

#### Scenario: Reference resolves to durable authority
- **WHEN** a `Covers` entry names a capability, requirement, or scenario that exists
- **THEN** the compiled capsule carries that authority and its derived Acceptance

#### Scenario: Separator collision is named
- **WHEN** a `Covers` reference cannot resolve and the target capability contains a requirement or scenario whose own name contains the ` / ` separator
- **THEN** the `unresolved-covers` diagnostic states that the name contains the separator and cannot be referenced
- **AND THEN** the author is not left to infer the cause from a reference that looks correct

#### Scenario: Over-segmented capability reference does not degrade silently
- **WHEN** a `Covers` reference carries more segments than the hierarchy allows and its first segment names a capability whose spec exists
- **THEN** it is reported as an unresolved reference rather than accepted as a free-text reference
- **AND THEN** a free-text reference whose first segment names no existing capability is still accepted unchanged

### Requirement: Task modes and conditional fields are executable
Keel MUST compile each task against its declared mode and reject conditional fields that the mode does not authorize. Where a diagnostic requires the author to add a field, it MUST name that field and its exact line prefix rather than describing the authority abstractly.

#### Scenario: Mode governs required fields
- **WHEN** a task declares `implementation`, `diagnose-only`, or `plan-first`
- **THEN** the required and permitted fields follow that mode

#### Scenario: Authority diagnostic names the field to add
- **WHEN** a task's `Covers` references an unresolved `Q<n>` and no authorized fallback is declared on the task
- **THEN** the `unresolved-authority` diagnostic names the `Autonomy boundary:` field and the `Pre-authorized fallback:` line prefix it requires
- **AND THEN** the diagnostic does not imply that prose in `design.md` satisfies the check
