## Why

`keel --check` prints a dry-run install plan that omits the OpenSpec overlay refresh entirely, so it can report an empty plan while `keel --install` rewrites files ([#27](https://github.com/TanglmChris/keel/issues/27)). A dry-run whose whole purpose is "show me what you will do" and which then under-reports is worse than none: it offers a promise a reader can rely on and does not keep it.

Investigating it turned up a second, opposite error in the one place overlays *are* mentioned. `keel --install --dry-run` announces "would refresh" for **every** surface without reading any of them, so with one stale marker out of six it claims all six would change.

So both dry-run surfaces are wrong, in opposite directions: one says nothing will happen when something will, the other says six things will happen when one will.

## What Changes

- The dry-run overlay branch classifies each surface the same way the real run does — refresh, current, missing — by computing the merged content and comparing it, instead of listing every surface unconditionally. It reports only what would change, and summarises the rest in the same `refreshed=/current=/missing=` shape the real run prints.
- `keel --check` runs that overlay dry-run as part of its plan, so its output covers every write `keel --install` would perform.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `keel-target-surface-diagnostics`: a dry-run must account for every write the corresponding real run would make, and must not name writes that would not happen.

## Impact

- `bin/keel.js` — the dry-run branch of `refreshOpenSpecSurfaceOverlay`, and the `check` action.
- `scripts/validate_plugin.py` — a scenario asserting dry-run and real run agree.
- User-visible: `keel --check` gains overlay lines when overlays are stale, and `keel --install --dry-run` stops over-claiming. No install behavior changes; only what the dry-runs say about it.
