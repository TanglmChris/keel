## Why

Keel #550 established two avoidable migration failures. A target can omit native history fields even when turn IDs and terminal states agree, and a source can acknowledge unsubscribe before it gives up the native writer.

## What Changes

- Check target identity and complete persisted history during planning and again before applying the handoff.
- Verify the original source is unloaded before attempting target acquisition. Preserve the existing writer refusal, verification, and explicit reconciliation behavior.

## Capabilities

### Modified Capabilities

- `keel-codex-host-team`: earlier target validation and verified source unload for an owned endpoint migration.

## Impact

Owned migration CLI, integration tests, and operator documentation. The change uses existing native methods and plan schema. The deployed roles, effective policy, and host configuration are outside this change.
