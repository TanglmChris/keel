## Why

Issue #236, reported by rtl_ppa_flow on 2026-10-05 and seen in this repository's own changes: a task's Evidence often already holds `Contract`, `Blocker`, and `Reauthorizations` when `keel gate task-start --record` runs. The gate then appends every missing slot at the end of the block, after `Reauthorizations:`. A session that rewrites the block in template order no longer matches the pending lines, leaves them behind, and `task-complete` reports duplicate or unexpected labels. It cost flow a round trip.

## What Changes

- `--record` places each missing slot directly after the nearest slot that precedes it in the template order and that the block already holds, or first in the block when none does. A partly written block comes out in template order.
- The template order is the one `capsuleSlots` and the bundled tasks template already share: Contract, each check's bare, `.red`, `.green`, and `.detects` slots, Review, Blocker, Reauthorizations.

## Capabilities

### Modified Capabilities
- `keel-core-gates`: `--record` places added slots in template order.

## Impact

`src/core/gates.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
