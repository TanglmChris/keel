## ADDED Requirements

### Requirement: A gate whose contract failed to compile derives no problem from a schema fallback

When a contract carries diagnostics and is therefore unusable, `task-complete` MUST report those diagnostics and MUST NOT additionally report a problem derived by falling back to a field of the other task schema. A compact v4 task declares no `Commands`, so a fallback that reads `Commands` reports the absence of a field the author never chose to declare, alongside — and ahead of — the diagnostic that actually explains the failure.

Suppressing that derived problem MUST NOT change any gate verdict. The compiler's diagnostics are reported whenever the contract is unusable, so a gate that would have failed on the derived problem alone cannot exist.

Per-check evidence validation MUST remain unaffected, because a genuine expanded v3 task still yields real check labels from that field.

#### Scenario: An unusable contract reports its diagnostics alone
- **WHEN** `task-complete` runs on a compact task whose contract carries a diagnostic
- **THEN** the reported problems name the field that carries the diagnostic
- **AND THEN** no problem states that `Commands` must define at least one `M<n>`

#### Scenario: Suppression does not turn a refusal into a pass
- **WHEN** the derived verification-form problem is suppressed because the contract is unusable
- **THEN** the gate still returns `fail` on the compiler's own diagnostics

#### Scenario: A task declaring no verification form is still refused, naming the compact field
- **WHEN** `task-complete` runs on a task declaring neither `Verify` nor `Commands`
- **THEN** the gate refuses it and the refusal names `Verify` as the field to add
- **AND THEN** no problem names `Commands` as a field that must define checks
