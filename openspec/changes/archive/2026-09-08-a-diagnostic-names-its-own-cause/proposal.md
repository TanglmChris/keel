## Why

Issue #112 is a usage report from an RTL PPA project that ran two Full-mode changes — 14 gated tasks, 149 keel invocations — and measured what the discipline cost. Three of its findings are about the same thing: a gate that knows something useful and says it at the wrong time, in the wrong place, or too many times. All three reproduce unchanged on 5.52.0.

**A derived problem is reported first, and as someone else's fault.** When an `M<n>` declaration carries an unfilled slot, the contract does not compile, and the completion path falls back to `commandLabels(task)` — which reads the expanded v3 `Commands` field a compact v4 task never declares. The declared-check set becomes empty, so `Resolved here: M2` is reported as naming a check the task does not declare, and that message prints *before* the real one. The reporter calls it "the only diagnostic in 149 invocations that made me edit the wrong file". The hazard is already known: the comment guarding `missing-commands` says the fallback's empty result is "a fact about the fallback, not about the task", and the guard was not extended to the references.

**The cheapest rule is learned at the most expensive moment.** A red-green strategy requires per-check `.red`/`.green` Evidence, and that is checked only at `task-complete` — after the capsule was written, the task implemented, the checks run, and the Evidence recorded. The `Verify` block is complete at `task-start` and the Evidence is all `pending`, so which checks will owe red and green is statically knowable there. The reporter hit this three times; this session hit it twice more.

**A rule explanation is printed once per violating item.** Measured on a two-check task: an 827-character failure in which the same 84-character sentence appears four times. It scales with the number of checks, and the reporter estimates a third of failure output is this repetition.

## What Changes

- The declared-check set is parsed from the task's own verification form rather than reconstructed from a field a compact task never has, so a reference to `M2` is never reported as undeclared because something else about `M2` failed to compile.
- `keel gate task-start` warns which checks will owe `.red`/`.green` Evidence under the declared strategy, and which are exempt. It is a warning: nothing new is refused.
- A gate problem may carry a shared rule explanation. The text renderer prints each specific problem, then each distinct explanation once.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-core-gates`: a reference is judged against what the task declares, the red-green obligation is stated when the contract is accepted, and a shared explanation is printed once.

## Impact

- `src/core/task-contract.js` — one exported label parser.
- `src/core/gates.js` — the completion label source, one new warning, and the text renderer.
- `scripts/validate_plugin.py` — three new scenarios.
- No verdict changes: nothing that passes today fails, and nothing that fails today passes. The unfilled-slot problem is still reported and still refuses; only the misleading second problem beside it goes away.
