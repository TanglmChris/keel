## Why

#186 reports that `keel openspec update` deletes Keel overlays and doctor can report Claude healthy while Codex is missing its task gates.

## What Changes

- Replay overlays for every repository-installed target after a successful OpenSpec update.
- Report overlay health for all installed targets, even when doctor selects a different target.
- Preserve upstream failure status and skip absent surfaces; do not install targets.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-openspec-surface-overlay`: update recovery and repository-wide overlay diagnostics.

## Impact

CLI routing and overlay discovery in bin/keel.js, behavioral regression scenarios, and published documentation. No dependencies or host hook changes. #190 remains a separate change.
