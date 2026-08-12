## ADDED Requirements

### Requirement: A change declares checks that run once for the whole change
`tasks.md` MAY declare a `## Change Verify` section (a `Strategy:` line plus one or more `C<n>: <check>` entries, contiguous and ordered from `C1`) and a matching `## Change Evidence` section (one `C<n>: <result>` entry per declared check). A `(regression)`-tagged `M<n>` check's bare Evidence MAY read `deferred to C<n>` in place of its own result. `task-complete` MUST require that a referenced `C<n>` is declared in `## Change Verify`. `change-close` MUST require every declared `C<n>` to carry concrete `## Change Evidence`. Neither section is required for a change no task's Evidence defers to.

#### Scenario: A regression check defers to a change-level check
- **WHEN** a `(regression)`-tagged `M<n>` check's bare Evidence reads `deferred to C1` and `## Change Verify` declares `C1`
- **THEN** `task-complete` does not require `M<n>`'s own concrete result
- **AND THEN** `change-close` requires `## Change Evidence` to carry concrete evidence for `C1`

#### Scenario: Only a regression-tagged check may defer
- **WHEN** an untagged `M<n>` check's bare Evidence reads `deferred to C1`
- **THEN** `task-complete` fails, naming the check and stating that only a `(regression)`-tagged check may defer

#### Scenario: A deferred check must resolve
- **WHEN** an `M<n>` check's Evidence defers to a `C<n>` that `## Change Verify` does not declare
- **THEN** `task-complete` fails, naming the unresolved label

#### Scenario: Deferral without a Change Verify section is refused
- **WHEN** any task's Evidence defers to a `C<n>` and `tasks.md` declares no `## Change Verify` section
- **THEN** `change-close` fails, naming the missing section

#### Scenario: A change with no deferred check needs neither section
- **WHEN** no task's Evidence defers to a change-level check
- **THEN** `change-close` reports nothing about `## Change Verify` or `## Change Evidence`, whether or not either section is present

#### Scenario: Change Verify labels are contiguous and concrete
- **WHEN** `## Change Verify` declares labels that are non-contiguous, duplicated, or carries a non-concrete check
- **THEN** `change-close` fails, naming the shape problem

#### Scenario: A declared change-level check needs its own evidence even when unreferenced
- **WHEN** `## Change Verify` declares a `C<n>` that no task's Evidence defers to
- **THEN** `change-close` still requires concrete `## Change Evidence` for that `C<n>`
