## Why

`packaged_openspec_schema_install_paths()` resolves its root under `dist/`, a path `validate_plugin.py` itself asserts must not exist. It returns `[]`, and its six call sites are all `for … in <empty>` assertion loops. So whether `keel --install` writes the OpenSpec schema into a consumer repo — and whether `--uninstall`/`--clear` remove it — has no verification at all, while `keel-openspec-surface-overlay` requires that behavior ("install Keel schema and managed authoring/apply/archive overlays"). A check that fails by doing nothing produces no signal and occupies the slot a real check would hold. Tracked as [#18](https://github.com/TanglmChris/keel/issues/18).

## What Changes

- Repoint the helper at the root the installer actually reads (`assets/openspec/schemas/keel-spec-driven/`) and make it raise when that root is absent, matching `install_to_repo.py:352`, so a future layout change fails loudly instead of silently emptying six assertions.
- Clear the remaining references to the retired `dist/` and `src/assets/` trees: delete `run_keel_hook` (zero callers), the `compact-task-authoring` projection loop, and the duplicated `("source", …), ("dist", …)` pass in `validate_openspec_schema`; repoint the two package-hygiene loops at the roots `package.json` actually ships.
- Add a scenario that fails when the helper's derived path set is empty, so the defect class — a derived set silently collapsing to nothing — cannot recur unobserved.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `keel-validation-runner`: a validator assertion driven by a derived set MUST fail when the set is empty rather than pass vacuously; helpers that resolve a packaged asset root MUST fail loudly when the root is missing.

## Impact

- `scripts/validate_plugin.py` — the only product file. Helper repointed; five dead-reference sites removed; one scenario added.
- Restored coverage lands in four existing scenarios: `cli`, `uninstall`, `thin-native-install`, `native-plugin-install-matrix`.
- **Risk / open outcome:** these six assertions have never executed. If they pass on first run the change is pure coverage restoration; if any fails, it has found a real product defect that hid behind the vacuous check. That case is out of this change's Touch and stops for reauthorization rather than being fixed inline.
- No consumer-facing behavior changes; no CLI, protocol, or gate semantics change.
- `keel/CHANGELOG.md` and the issue are updated at close.
