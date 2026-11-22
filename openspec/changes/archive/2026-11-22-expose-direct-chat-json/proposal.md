## Why
Keel #552 reports stored ordinary DMs that Kaiwu cannot dispatch because recipient metadata is missing from public JSON when the repository has no role renames.

## What Changes
Project canonical direct-group participants on all existing JSON read surfaces. Retain ordinary group messages, no-wake and canonical role naming behavior. No changes to persistence or read cursors.

## Capabilities
### Modified Capabilities
- `keel-cross-host-mailbox` — predictable direct recipient metadata on reads.

## Impact
Keel chat read projection and focused public CLI regression. Kaiwu downstream acceptance is coordinated separately in Kaiwu #561.
