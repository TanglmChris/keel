# diagnostics-name-the-cause

## Why

Issue #28 reports a real change costing roughly eight extra gate round-trips, every one an authoring-format problem rather than a design problem. Four of its findings are confirmed open against 5.3.6, and they share one shape: the gate knows exactly what is wrong and reports something else.

- Citing a resolved question in `Covers` prose re-opens it. `field(task, "Covers").match(/\bQ\d+\b/g)` scans the whole field, so `F13 (Q1 resolved -> XHR)` is read as an open `Q1` and demands a pre-authorized fallback. The reporter's only available fix was to delete the strings `Q1`/`Q2` from their traceability text — the gate punished the correct authoring.
- A non-concrete `M<n>` check says only "must define a concrete public check". The cause is an unfilled slot token that `unfilledToken` already identifies and already names for `Verify`; the per-check message never calls it.
- A task that declares no verification at all is reported as an expanded v3 task missing nine fields, seven of which have documented defaults or belong to `Coupling: required`. The one actionable line is buried last.
- `task-complete` without `--task` infers the first unchecked task. When that task has never started, its readiness problems are printed under a heading the author reads as "the task I just finished failed".

Left alone, each one costs the same round-trips again, and the first actively teaches authors to write worse `Covers`.

## What Changes

- `Covers` question references are matched structurally at the head of an entry, so naming a resolved question alongside the fact that closed it no longer blocks implementation.
- `missing-command-check` names the unfilled token it matched, the way `non-concrete-verify` already does.
- Compact-v4 detection covers the absent-`Verify` case, and the expanded v3 required set is reduced to the fields that have no documented default, so a missing verification declaration reports as one problem.
- `task-complete` refuses to infer a task that has recorded no capsule fingerprint, naming both the inferred task and the most recently checked one.

## Impact

- `src/core/task-contract.js`, `src/core/gates.js`
- `scripts/validate_plugin.py`
- Specs: `keel-task-capsule`, `keel-core-gates`, `keel-validation-runner`
- `AGENTS.md` and the shipped tasks template where they state the affected rules

## Non-goals

- Issue #28 items 2 and 3 (template gaps) and item 7 (spec template) belong to a separate templates change; item 8 is upstream OpenSpec CLI; items 1 and 10's second half already shipped.
- No change to the write guard's path scope (#28 item 10 first half), which is unverified and separately owned.
