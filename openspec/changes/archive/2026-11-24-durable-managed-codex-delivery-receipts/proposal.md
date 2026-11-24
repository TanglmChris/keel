## Why

Keel #544 needs a durable execution reference before resource reconciliation. A managed Codex delivery claim currently remembers a turn ID but can lose the thread identity when the role hands over. Reading the current native role is insufficient after a handover or host disconnect.

## What Changes

Persist the original thread in new managed delivery claims. Add an offline delivery status query to report what the recorded claim establishes, including ambiguity for legacy claims.

## Capabilities

### Modified Capabilities

- `keel-portable-task-execution`: durable native receipt lookup without re-dispatch.
