## ADDED Requirements

### Requirement: The review checklist does not restate mechanical refusals

`keel-review-checklist` MUST NOT direct the agent to confirm evidence shape that `keel gate task-complete` already refuses on its own — a missing or drifted Contract anchor, or missing `.red`/`.green` Evidence for a red-green check — and MUST keep the judgments the gate cannot make, including that an evidence-first task names its observable proof and that behavior checks prove Acceptance.

#### Scenario: The checklist names only what the gate cannot judge
- **WHEN** a reader opens `keel-review-checklist`'s Deterministic gate check, in source and in the shipped copy
- **THEN** it does not instruct confirming the Contract line's fingerprint or the presence of `.red`/`.green` Evidence
- **AND THEN** it still states that evidence-first tasks name their observable proof and that behavioral checks must prove Acceptance through the public interface
