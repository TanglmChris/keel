## Why

Issue #479, approved by the owner on 2026-10-26, who chose to collapse whitespace on both sides. A `Fails with:` literal that holds a run of spaces can never match its red. `task-contract.js` collapses whitespace in the whole check text before it extracts the literal, so `` `FAIL  name` `` is stored as `FAIL name`. `gates.js` then looks for that in the raw `.red` Evidence, which still holds the two spaces. Tool output often aligns with runs of spaces (kaiwu-ip's fast check prints `FAIL  <name>`, pytest prints `E       assert …`), and kaiwu-ip hit this on 2026-10-26 in `fast-check-records-live` task 1.1. It passed only by pasting a second, single-spaced copy into the Evidence.

## What Changes

- **Declared literals and recorded Evidence are compared with every run of whitespace read as one space.** That covers `Fails with:` against `.red`, `Detects:` against `.detects`, and `Measured:` against the bare `M<n>` Evidence. Spacing, line breaks, and indentation stop deciding the outcome. The characters themselves still must appear.
- **The refusal says so.** Each refusal states that runs of whitespace are compared as one space, so an author can rule spacing out as the cause.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-core-gates`

## Impact

`src/core/gates.js`, `scripts/validation/contract.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
