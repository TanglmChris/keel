## Why

Issue #95 (owner-filed, 2026-08-11): a check that only needs to run once for a whole OpenSpec change — a full three-layer regression suite, a byte-baseline comparison across tasks — has no place to live in the current protocol. Every `M<n>` lives on one task, and Evidence is recorded and checked per task at `task-complete`, the only point that reads it. An author who wants "run once, and gate every task on it" has three costed options today, all named in the issue: repeat the check on every task (Nx runtime, Nx Evidence — the issue's own reproduction cites three full regression runs, roughly engine 632s + backend 161s + frontend 669s across 64 files, cut to one by hand); attach it only to the last task (a silent hole — an earlier task can `task-complete`, and even be individually archived, with the full-suite guarantee never having run); or drop it.

Reproduced directly against the current tree (2026-08-12, 5.38.0): `completionChecks()` in `src/core/gates.js:758-792` validates a `(regression)`-tagged `M<n>` check's bare Evidence with nothing but `isConcrete()` (line 759). Any concrete text passes, including text that claims to defer to a check that was never declared anywhere, never ran, and does not exist — there is no section of `tasks.md` a change-wide check can be declared in, and no gate reads one. `changeClose()` (`src/core/gates.js:1196-1301`) validates `## Invalidates` and `## Expectation Coverage`, both change-level sections, but has no equivalent for a once-per-change verification check.

## What Changes

- `tasks.md` gains two optional, change-level sections: `## Change Verify` (a `Strategy:` line plus one `- C<n>: <check>` line per check that runs once for the whole change) and `## Change Evidence` (one `- C<n>: <result>` line per declared check). Both are absent by default and cost nothing to a change that does not use them — the trigger is use, not declaration.
- A `(regression)`-tagged `M<n>` check's bare Evidence may read `deferred to C<n>` instead of recording its own result, when `C<n>` is declared in this change's `## Change Verify`. `task-complete` for that task then requires only that `C<n>` resolves — not that it has already run. `change-close` requires every declared `C<n>` to carry concrete `## Change Evidence`, once, for the whole change.
- A non-regression check that tries to defer, or a `C<n>` that resolves to nothing declared, is refused with a diagnostic naming what is missing.
- No change to `task-contract.js`'s compiled capsule shape, the `(regression)` tag itself, or any diagnostic outside this deferral path — an unrelated task's fingerprint does not move.

## Capabilities

### Modified Capabilities
- `keel-core-gates`: gains change-level `## Change Verify` / `## Change Evidence` sections and the `deferred to C<n>` Evidence disposition for `(regression)`-tagged checks, validated at `task-complete` (structural resolution) and `change-close` (completeness).

## Impact

- Affected code: `src/core/gates.js` (`completionChecks`, `taskComplete`, `changeClose`, new section parsers).
- Affected docs: `AGENTS.md` (and its synced copies) verification-discipline section.
- Affected tests: `scripts/validate_plugin.py` (new scenario).
- No change to `src/core/task-contract.js`, no new dependency, no schema version bump — `keel-task-capsule/v1` capsules are unaffected because the deferral lives entirely in Evidence, which the capsule never compiles.
