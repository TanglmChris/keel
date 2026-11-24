## ADDED Requirements

### Requirement: Inspect a durable managed Codex delivery receipt

Keel MUST bind new managed delivery claims to the recorded thread before submitting a turn and retain that thread with an acknowledgement. The managed role receipt query MUST use durable local claims. The query MUST NOT infer thread identity from the current role for an older claim or treat an uncertain submission as a native acknowledgement.

#### Scenario: The source role has handed over
- **WHEN** a receipt is queried by its record ID after a managed role changes thread
- **THEN** the query reports the recorded acknowledgement with the original thread and turn without contacting either native thread

#### Scenario: A claim is pending or predates the stored thread ID
- **WHEN** a claim has no acknowledgement or lacks its original thread reference
- **THEN** the query preserves known fields and explicitly reports unknown submission or missing provenance without creating or retrying a turn
