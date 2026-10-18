## Why

Issue #342 (rtl_ppa_prj, 2026-10-03 and 2026-10-13): after a Keel CLI upgrade every checked task reported contract drift, and the only way to archive was `task-start --record --keep-evidence`, a claim Keel says it does not verify. Measured 2026-10-18 by recompiling rtl_ppa_prj's own commits under the released CLIs:

- 2026-10-03, `add-iecc-cbbs#2.1`: a real compiler change. Commit `3b63c5e4` compiles to the recorded `c7f56b…` under 5.78–5.80 and to `7da362…` from 5.81.0 on (#177 fingerprints a cited multi-line decision whole); the capsules differ only in `authority[4..5].text`.
- 2026-10-13, `fast-check-waivers#1.1`: not the compiler. 5.123.0 and 5.125.0 compile each commit identically; between the recording commit `7859598b` (`1cd0a8…`) and `aee9fa7d` (`567751…`) the one changed field is `boundaries.autonomy`, the inherited standing-authorization entry, after `keel/config.yaml` replaced `push:main` with `push-protected:main@iecc-pm`.

In both cases Keel had what it needed to say so: the commit that recorded the anchor is in Git, and the current compiler can compile it.

## What Changes

- `task-start --record` writes the Keel version beside the fingerprint: `- Contract: keel-task-capsule/v1 sha256:<hex> (keel <version>)`.
- On drift, the gates and `keel context` find the commit that recorded the anchor, compile that commit's task sources with the running compiler, and name the cause: the changed capsule fields when that commit reproduces the anchor; a compiler change when it does not, the anchor records another Keel version, and the commit compiles to today's fingerprint; otherwise the existing message, claiming nothing.
- A compiler-only drift still needs `task-start --record` (owner, 2026-10-18), and that re-record says the evidence stands, verified, with no `--keep-evidence` claim.
- `change-close` does not count as drift a checked task whose only change since its recording commit is the inherited standing authorization (owner, 2026-10-18); it warns once naming the task.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-core-gates`: drift names its cause; a compiler-only re-record keeps evidence verified; a completed task is not drifted by a standing-authorization change.

## Impact

New `src/core/drift.js`; `src/core/gates.js`, `src/core/context.js`, `src/core/task-contract.js`; `scripts/validate_plugin.py`; `README.md`; one published spec; the changelog.
