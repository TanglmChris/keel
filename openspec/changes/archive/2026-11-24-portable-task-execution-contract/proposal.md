## Why

Keel #544 needs a stable task view for upper applications. Existing dispatch and recovery use separate Codex and Claude session identities, while a Keel todo already provides a durable reference to the requested work.

## What Changes

- Draft a shared contract for task identity, execution ownership, progress, and result evidence.
- Define prerequisites for normal tick changes and exceptional continuation, using the measured Codex and Claude baseline.
- Keep the existing OpenSpec gate contract for work already using it.

## Capabilities

### New Capabilities

- `keel-portable-task-execution`: one task view with a stable identity across native execution instances.

## Impact

The next implementation slice is a shared task record and projection. Scheduling, automatic recovery and changing workflow defaults are later slices with distinct behavioral acceptance.
