## Why

The contract anchor exists to answer one question: did the task's authority change while it was being implemented? Two of the three surfaces that promise to answer it do. `keel context` compares the recorded fingerprint against a fresh compile, and `keel guard status` compares it against the manifest. The completion gate — the one the protocol names in the same sentence, the one that decides whether a task is finished — only checks that sixty-four hex characters are present.

Measured on 2026-08-01 against `ad9af24`: a task whose anchor was replaced with sixty-four zeros passes `task-complete` with zero problems. A task whose Touch was rewritten from `src/feature.js` to `src/DRIFTED.js` after recording also passes — and the gate's own JSON payload prints the recompiled `2ca3e03d…` beside the recorded `241984…` in the same breath. It holds both numbers and does not compare them. `change-close --action sync` passes the same forged anchor.

The specs already say otherwise. `keel-touch-write-guard` states that a contract edit is caught because `keel gate task-complete` "refuses the recorded anchor, because both compile the capsule and compare it". `keel-core-gates` states that a recorded anchor "is compared against the recompiled fingerprint". Neither was true. This is the defect class 5.7.1 named — a check whose form is valid and whose content is never examined — sitting inside the mechanism the rest of the protocol's drift detection rests on.

The shipping scenario that claims to prove the comparison is itself the proof it never ran: `completion-requires-a-recorded-anchor` records the fingerprint of one change and writes it into a different change's tasks.md. Those two values differ, because a compiled capsule names its own source paths. It passes today. It cannot pass once the comparison exists.

## What Changes

- **A recorded anchor is compared, not counted.** `task-complete` recompiles the capsule — which it already does — and refuses when the recorded value differs. Drift is a hard failure, not a warning, because the protocol says drift hard-stops and returns to authoring.
- **The refusal says what the re-record warning already says.** `task-start --record` already warns that evidence produced under a previous contract is stale. A completion refusal that said less than that warning would be the weaker half of one mechanism.
- **`change-close` compares too.** The issue named `task-complete`. Stopping there would leave the window between "every task checked" and "the change archived" completely open, at the one gate whose whole job is closing a live change — and it already compiles every task's contract, so the comparison is free. This extension is deliberate and is recorded here rather than smuggled into the fix.
- **The `keel-task-capsule/v1` prefix stays optional.** A fingerprint is a digest over the canonical capsule serialization, so a value that matches could only have come from the schema that produced it — the prefix proves nothing the comparison does not already prove. It earns its place inside the drift message, where a reader needs to know which schema compiled which value.
- **The dishonest fixture is repaired, not accommodated.** `completion-requires-a-recorded-anchor` will record its anchor on the change it completes.

## Capabilities

### New Capabilities
<!-- None. Two shipped requirements are made true. -->

### Modified Capabilities
- `keel-core-gates`: the completion gate compares the recorded anchor against the recompiled fingerprint and refuses a difference; `change-close` applies the same comparison to every checked task of a live change.

## Impact

- **Code**: `src/core/gates.js`, and the validator scenarios covering both gates.
- **Behavior change**: a task whose contract was edited after recording now fails where it previously passed. That is the point, and it is why this is a minor release rather than a patch. Recovery is the documented one — `keel gate task-start --record` reauthorizes and the gate's message names it.
- **Blast radius**: any live change in any consuming repository whose anchors have drifted will start failing at completion. No archived change is affected: `gates.js` excludes the archive tree from change discovery, so an archived anchor is never recompiled, which is the boundary `keel-core-gates` already states.
- **Cost**: zero new work. `taskComplete` compiles the contract at `gates.js:623` and `changeClose` compiles every task's at `gates.js:881`. Both already hold the value they were not comparing.
- **Risk**: the comparison is only as trustworthy as the compiler's determinism. If `compileTaskContract` were unstable across runs, this would turn a silent gate into a gate that refuses correct work. The `anchor-reverification-bound` scenario already asserts that a live anchor recompiles to its recorded value, so the property is under test before this change depends on it.
- **Dependencies**: none added.
