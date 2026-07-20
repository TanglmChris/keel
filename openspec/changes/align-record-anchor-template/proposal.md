## Why

The `keel-spec-driven` tasks template ships the Contract evidence anchor as
`- Contract: pending task-start capsule and fingerprint`, and
`scripts/validate_plugin.py` requires that exact long form. But the
`keel gate task-start --record` matcher (`src/core/gates.js`) and the
`keel-core-gates` "Explicit record replaces only the pending anchor" scenario
both require the literal line `- Contract: pending`. So `--record` refuses on a
freshly-scaffolded task with `record-refused` until the author manually trims the
anchor — the same author-surface-versus-validator disconnect family as issue #1,
found while dogfooding Change 1.

## What Changes

- Emit the template's Contract anchor as the literal `- Contract: pending` in both
  the `openspec/` and `assets/openspec/` template copies, keeping the "anchored by
  `keel gate task-start --record`" guidance as a comment.
- Update the `validate_plugin.py` template Contract-anchor needle from the long
  form to `- Contract: pending`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: the shipped tasks template emits a `--record`-compatible
  `- Contract: pending` anchor, so a freshly-scaffolded task can be anchored
  without manual editing.

## Impact

- Assets: both `keel-spec-driven` tasks template copies.
- Validator: the template Contract-anchor needle.
- Closes the `--record` template-anchor disconnect found during dogfooding.
- Folds into the held, unpublished 5.2.0.
