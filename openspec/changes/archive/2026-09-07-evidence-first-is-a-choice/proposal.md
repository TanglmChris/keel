## Why

`keel-task-capsule` carries a requirement scenario literally named **"Evidence-first is explicit"**, scoping the strategy to "a docs, configuration, diagnosis, or other non-behavioral task [that] cannot use a meaningful red-green loop". The implementation makes it the opposite: `verification()` in `src/core/task-contract.js` resolves a missing `Strategy:` to `evidence-first`, and the compiled capsule records that value as though the author had written it — no problem, no warning, at either gate.

Measured directly against the gates: a task with no `Strategy:` line passes `task-start` and `task-complete` with no red-green evidence; the same task declaring `vertical-tdd` fails `task-complete` naming the missing `M1.red` and `M1.green`. **Omitting a line is how a task opts out of red-green**, and nothing on screen says so.

Measured across six repositories, 1,127 tasks declare a verification form. 961 declare a strategy and 166 do not. Of the 961, `evidence-first` is chosen 299 times — 17% of tasks in `chip_sec_flow_v2` and 38% in Keel itself, against 89% in `dasauto` and 92% in `my_xhs`. A repository in which nine tasks in ten "cannot use a meaningful red-green loop" is not what that scenario describes; it is the escape hatch being used as the default road.

## What Changes

- `keel gate task-start` refuses a task that declares a verification form but no `Strategy:`, naming the supported strategies — the same diagnostic shape as the existing unsupported-strategy refusal. The strategy stops being a silent default.
- `evidence-first` requires a `Reason:` line under `Verify`, stating why the task cannot use a meaningful red-green loop. `task-start` refuses an `evidence-first` task without one, or with a placeholder.
- The gate checks that the reason is present and concrete and never that it is true — the same contract `Discard reason:` already has. Truth stays with the semantic Review.
- **No exemption**, including `diagnose-only`: an exemption keyed on a field the author also writes is a second escape hatch.
- `Reason:` is parsed as a `Verify` field beside `Strategy:` rather than as a check. Today such a line is refused as a malformed command entry.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-task-capsule`: the verification strategy is declared rather than defaulted, and `evidence-first` carries a stated reason.
- `keel-core-gates`: `task-start` refuses an undeclared strategy and an unjustified `evidence-first`.

## Impact

- `src/core/task-contract.js` — `verification()` and the required-field set.
- `src/core/gates.js` — the `task-start` problem set.
- `scripts/validate_plugin.py` — one new scenario.
- Existing tasks: 299 `evidence-first` tasks and 166 strategy-less tasks exist across the surveyed repositories. The gates run on live changes and already refuse an archived one, so the historical corpus is unaffected; a live change carrying either shape is refused until its author declares what it meant.
- Risk: an author writes a rote reason. Accepted — it is the same exposure `Discard reason:` carries, and a rote reason is at least a sentence a reviewer can disagree with, where a silent default is not.
