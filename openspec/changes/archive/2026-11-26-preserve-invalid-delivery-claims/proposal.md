## Why
Kaiwu #577 reproduced a second native turn for the same record when a persisted claim was damaged to null. Keel 5.231.12 used truthiness in both the receipt and delivery paths.

## What Changes
Use the recorded key's presence to distinguish absence from unknown outcomes. Apply the same decision to the public receipt and retry paths.

## Capabilities
- Modified: `keel-codex-host-team` covers invalid delivery claims.

## Impact
Managed host and public CLI regression. Existing state and receipt shapes are retained.
