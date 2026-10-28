## Why

Issue #496, approved by the owner on 2026-10-28 as recommended. A shift feature bug fix, within the 2026-10-14 freeze. Since 5.212.0 (#491) a guard manifest whose task is checked and whose change is archived enforces nothing: the write guard hook lets every write through and `keel guard status` reads `archived`. Three other places decide "is a task's write guard active" by whether `keel/guard.json` exists, so they still treat that manifest as a live guard: `keel shift check` reports `task-in-progress` and exits 1, which blocks a hand-over on a file that guards nothing; `keel context` defers a standing-authorized protocol refresh; and `keel --update --adopt` leaves the session alone as "under a task's write guard".

## What Changes

- **One test of whether a guard is in force,** taken from `keel guard status`: a manifest that is absent or `archived` holds nothing, and every other state (`active`, `completed`, `drifted`, `invalid`) still holds, because the hook still denies writes under each of them.
- **`keel shift check`** reports an archived manifest as a note naming `keel guard clear`, not as a `task-in-progress` item.
- **`keel context`** does not defer the protocol refresh for an archived manifest.
- **`keel --update --adopt`** restarts an idle session whose worktree holds only an archived manifest.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`
- `keel-stateless-continuity`

## Impact

`src/core/guard.js`, `src/core/shift.js`, `src/core/context.js`, `bin/keel.js`, `scripts/validation/shift.py`, `scripts/validation/hosts.py`, `scripts/validation/registry.py`, the published specs, and the changelog.
