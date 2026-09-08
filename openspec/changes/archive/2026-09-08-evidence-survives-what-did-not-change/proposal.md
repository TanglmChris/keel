## Why

Issue #112 records four re-verifications in one session caused by contract changes that could not have affected any evidence. The clearest is renaming `M2:` to `M2 (regression):` — a classification tag, with the assertion unchanged by a single character. In that project an `M<n>` check is a real experiment: one end-to-end run is 30–60 seconds, a nine-combination sweep is three minutes, and one of the four re-verifications meant **breaking a testbench, re-running, and restoring it** to re-observe a failure mode nothing about the tag had changed.

What the gate says today is a warning, and its own comment is honest about why:

> A re-record that lands a different fingerprint is a contract change, so any Evidence already produced under the previous one is stale. The gate cannot judge which Evidence survives; it names the change and leaves the call to the current agent's Review.

The gate is right that it cannot judge. The cost is that its only available sentence is *all of it is stale*, so an author acting on it in good faith re-runs everything — including the checks they can see were untouched.

## What Changes

- `keel gate task-start --record` accepts `--keep-evidence M1,M3`: the author declares which checks' evidence the contract change did not affect.
- The stale-evidence warning then names only the checks that were not kept, and states which were kept and by whose declaration.
- The kept labels must be checks the new contract declares; anything else is refused rather than silently ignored.
- `--keep-evidence` without `--record` is refused: there is no re-record for it to qualify.
- Nothing else changes. `task-complete` still requires every `M<n>`'s Evidence, still enforces red-green, and still runs the semantic Review. The flag removes a sentence that was too broad; it removes no check.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-core-gates`: a re-record may carry the author's declaration of which evidence survived it.

## Impact

- `bin/keel.js` — one flag.
- `src/core/gates.js` — validation of the declared labels and the narrowed warning.
- `scripts/validate_plugin.py` — one new scenario.
- **What this does not verify**: whether the declaration is true. The gate does not retain the previous capsule — only its digest — so it cannot compare a check's old text to its new one and cannot know whether an assertion changed. It validates that the named checks exist and reports the declaration; the claim itself belongs to the Reauthorizations note the protocol already requires, and is reviewed there. This is the same contract `Discard reason:` has, and it is stated rather than implied.
