## Why

Keel's own published specs are the artifact it asks every consumer to trust, and nothing in the repository ever checked that they satisfy the validator Keel ships. `openspec validate --specs --strict` appears in no scenario — measured 2026-08-02 at 5.16.0, `grep -c '\-\-specs' scripts/validate_plugin.py` returns 0.

The gap was not theoretical. Issue #46 measured **8 of 21 published specs failing** that command, every one of them on `Requirement must contain SHALL or MUST keyword`, because the requirement opened with a context paragraph and the strict validator reads only the block directly under the heading. Nothing surfaced it: every change's closing task validates *the change*, which passes, and `npm test` never ran the published store through anything.

Those 8 failures do not exist under the validator this repository pins, and never did. `node_modules/.bin/openspec` is 1.6.0 and reports 21 passed / 0 failed; bare `openspec` on PATH here is **1.4.1** and reports exactly the 13/8 split #46 records as a 1.6.0 result, naming the same eight specs. The issue measured a different program than the one it named — which is the drift `keel doctor`'s version cross-check exists to expose, landing on the report that was trying to use it.

So the store is at zero and has been. A check added at zero holds it there; added later it starts by recording a number somebody has to argue down.

## What Changes

- Validation asserts that every published spec passes `openspec validate --specs --strict`, and fails naming the specs that did not.
- The assertion is absolute, not a ratchet. Issue #46 proposed recording the current failure count and reducing it over time; that was the right shape when the count was 8 and is the wrong shape now that it is 0, because a recorded tolerance for failures is a place for new ones to hide.
- The scenario reports a skip rather than passing when the validator is unavailable, matching how the repository already treats a consuming tool that is not on PATH.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-validation-runner`: gains the requirement that the repository's own published spec store is validated by the tool Keel ships, on the same footing as the requirement that a shipped template is validated by the tool that consumes it.

## Impact

- `scripts/validate_plugin.py`: one scenario plus its registry entry.
- No change to `bin/keel.js`, the gates, or any runtime surface. This adds coverage of an existing artifact; it does not change what any command does.
- Risk: a future spec written in the repository's own house style — context paragraph first, modal verb after — now fails `npm test` where it previously merged silently. That is the intent, and the failure names the spec and the requirement, so the fix is moving the modal sentence into the first paragraph. It is a wording change with no semantic content.
- Risk: the check depends on the OpenSpec binary that answers, which 5.15.0 established may differ from what a repository declares. The scenario states the version it exercised, consistent with `keel-target-surface-diagnostics` already requiring validation to assert the OpenSpec version it is testing against.
- No new dependency.
