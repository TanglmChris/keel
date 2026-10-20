## Context

`keel-tdd-or-test-first/SKILL.md` (50 lines) lists the seven strategies with one line each, and explains `Fails with:` and `artifact` Evidence. `keel-guidance-tiering` lets a skill keep how-to prose in `guidance.md`, read unless `executor_tier: high`, and the suite checks a guidance file carries no criterion word (`MUST`, `SHOULD`, `refuses`, `rejects`, `hard-stops`). Only `keel-run-single-task-goal` has one today.

## Facts

- F1 — Archive usage, measured 2026-10-20 at `3c77015` over `openspec/changes/archive/*/tasks.md` (a script counting each task's `Strategy:` line, its checks, and its Evidence labels): 213 changes, 561 tasks. Strategies: `vertical-tdd` 279, `evidence-first` 231 (188 of them titled as a release or version task), `regression-first` 44, `rendered-behavior` 4, `characterization` 3, `snapshot-characterization` 0, `equivalence` 0. Red-green tasks: 323 with 891 checks, 375 of them tagged `(regression)`, 517 `.red` lines, none recorded as a passing red. `Fails with:` on 185 tasks, `Detects:` on 10, `Measured:` on 3, `deferred to C<n>` on 61. 61 tasks re-recorded their contract.
- F2 — The archive cannot say whether a strategy caught more defects: it holds only work that got through, so a false stop or a missed defect left no record there (#70), and no task records an independent acceptance result. Quality per strategy needs prospective sampling; #411 already asks for that measurement across the flow.
- F3 — #389's own constraints: do not reimplement the existing forms, do not add a CLI, configuration key, or strategy, and do not lower verification by model name.

## Decisions

- D1 — The selection table, examples, and the when-it-pays notes go in `src/skills/keel-tdd-or-test-first/guidance.md`, because they explain how to choose; the body keeps every criterion. The body gains the selection criterion (choose by what would make the Acceptance false; size, apparent risk, the executing model, and the cost of running a red do not choose the strategy) and the `Detects:` / `Measured:` contracts, each stated once, linking the spec rather than restating it.
- D2 — The new scenario `tdd-strategy-guide` reads the strategy list from `SUPPORTED_VERIFICATION_STRATEGIES` in `src/core/task-contract.js`, so a strategy added later without a row in the guidance fails the suite. It also checks the body names `Fails with:`, `Detects:`, `Measured:`, `(regression)`, `deferred to C`, and `artifact`, and that the plugin copy of `guidance.md` is byte-identical.
- D3 — The measurement in F1 and an evaluation plan for F2 are reported on #389 when it closes; the forward-looking quality measurement is owned by #411. No gate changes until that data exists.
