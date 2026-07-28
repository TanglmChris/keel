## Why

Three durable statements are no longer true, and none of them says so.

The consumer bootstrap says Touch bounds writes "for product files" but never names the record-layer exemption, so a consumer still infers that `tasks.md` belongs in Touch — the trap [#8](https://github.com/TanglmChris/keel/issues/8) reported. [#15](https://github.com/TanglmChris/keel/issues/15) held the wording back because the sentence did not fit the block's byte budget.

Live specs still require Keel to release as version `3.0.0` and to report base version `4.0.0`. [#22](https://github.com/TanglmChris/keel/issues/22) found one; a sweep found **seven** version-pinned statements across two capabilities, all of them false at 5.3.4. Meanwhile [#23](https://github.com/TanglmChris/keel/issues/23) reports the mirror defect: the `.codex/` overlay markers fall one version behind at every release because `bump_version.js` refreshes only `.claude/`. So the alignment requirement names a version that no longer exists, and the alignment it actually wants is unenforced.

The contract fingerprint is described as recompiled and compared at resume, projection, and completion — with no stated bound. [#24](https://github.com/TanglmChris/keel/issues/24) found that all 47 archived anchors fail to reproduce, because archiving renames the change directory and the capsule embeds that path in every authority `source`.

## What Changes

- The bootstrap names the record-layer exemption. Room is made by listing one guard opt-out (`--no-guard`) instead of two; measured at 1012 bytes against the 1024 budget, so the budget itself is not touched.
- The version-alignment requirement stops naming a historical version and states the invariant instead: every shipped marker agrees with the package version. Six obsolete version-pinned scenarios go with it.
- That invariant becomes enforced rather than asserted: a check compares every shipped marker against `PACKAGE_VERSION`, and `bump_version.js` refreshes the overlay markers of every initialized target, not just `.claude/`.
- The fingerprint guarantee states its bound: an anchor is reverifiable while its change is live, and becomes a historical record once the change is archived.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the release-alignment requirement becomes version-agnostic and enforced; its `3.0.0`/`2.7.0` scenarios are removed.
- `keel-native-plugin-package`: the `4.0.0` base-version scenarios are removed in favour of the same invariant.
- `keel-core-gates`: the fingerprint-comparison requirement states that it bounds live changes.
- `keel-openspec-surface-overlay`: overlay markers are refreshed for every initialized target by the release bump, not only the one the bump happens to touch.

## Impact

- `assets/bootstrap/AGENTS.md` — the one consumer-facing wording change; every other change here is repository-internal.
- `scripts/bump_version.js` — refresh all initialized targets' overlay markers.
- `scripts/validate_plugin.py` — a marker-alignment check and the bootstrap assertions.
- Four live specs, through `MODIFIED` and `REMOVED` deltas.
- `AGENTS.md` — the fingerprint sentence gains its bound.
- **Deliberately not done:** making archived fingerprints reproducible. Normalizing the archive path back to the live form would restore it, but the displayed `source` would then point at a path that no longer exists. Documenting the bound is the honest fix; see design D4.
