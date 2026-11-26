## ADDED Requirements

### Requirement: Independent Claude wake during managed delivery

A tick SHALL start managed Codex delivery and allow an independently bound, eligible ended Claude CLI session to resume while a managed receipt is pending. It SHALL record the successful wake before waiting for the pending receipt. Shift hand-over and patrol SHALL follow both wake operations.

#### Scenario: Another tick runs while the Codex receipt is held
- **WHEN** an independent Claude role has an addressed record and another tick runs after its successful wake but before a managed Codex acknowledgement returns
- **THEN** the later tick observes the recorded wake and does not resume that Claude session again for the same record
- **AND** an ambiguous Codex receipt remains subject to the existing claim checks
