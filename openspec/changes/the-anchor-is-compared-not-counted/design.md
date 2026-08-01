## Context

Everything Keel says about drift rests on one comparison. The compiled capsule fingerprint is recorded in a task's Evidence before implementation, and every later surface is supposed to recompile it and check. That is what makes a mid-flight Touch edit detectable at all, and it is why the write guard can afford to let a task write its own tasks.md — the record layer is safe precisely because the gates that compile the capsule catch a contract edit hiding in the same file.

The completion gate never performed the comparison. It parsed the anchor, validated its shape, and threw the value away.

## Goals / Non-Goals

**Goals:**
- A recorded anchor that no longer matches the task's contract stops the task, wherever a live change's contract is checked.
- The refusal tells the reader both values, why it stopped, and the one command that resolves it.
- The change costs nothing at runtime, because both gates already compile what they were failing to compare.

**Non-Goals:**
- No new anchor syntax, and no new required field. The anchor form that `--record` writes and the bare form a human writes both keep working.
- No recompilation of archived changes. That boundary is already stated and already scenario-bound.
- No relaxation anywhere. Nothing here makes a currently-failing case pass.

## Decisions

**F1** — `hasRecordedAnchor` (`src/core/gates.js:113`) is `Boolean(plan && anchoredFingerprint(plan.previous))`. The parsed digest is discarded; it is never compared with `compileTaskContract`'s result. *Basis:* source read, `ad9af24`.

**F2** — Two other surfaces do compare. `src/core/context.js:99` reports `Task contract fingerprint drift` when the anchor differs from the fresh compile, and `src/core/guard.js:241` reports `fingerprint-drift` when the recompiled capsule no longer matches the manifest. Completion is the outlier, not the norm. *Basis:* source read.

**F3** — Two shipped requirements already assert the behavior. `openspec/specs/keel-touch-write-guard/spec.md:49` — "`keel guard status` reports fingerprint drift and `keel gate task-complete` refuses the recorded anchor, because both compile the capsule and compare it". `openspec/specs/keel-core-gates/spec.md:342` — "the anchor is compared against the recompiled fingerprint as before". *Basis:* spec read. This change makes existing text true rather than adding a promise.

**F4** — Measured against `ad9af24`: an anchor of sixty-four zeros passes `task-complete` with an empty `problems` array. Rewriting Touch from `src/feature.js` to `src/DRIFTED.js` after recording also passes, with the recompiled `2ca3e03d1db0…` reported in the same payload as the recorded `241984884c67…`. *Basis:* reproduction run 2026-08-01, both branches observed directly.

**F5** — `change-close --action sync` passes the same forged anchor, reporting no problem once the change's unrelated `## Expectation Coverage` requirement is satisfied. It compiles every task's contract at `gates.js:881` and never reads the anchor. *Basis:* same reproduction.

**F6** — Both gates already hold the value. `taskComplete` compiles at `gates.js:623` and keeps it as `usableContract`; `changeClose` compiles per task at `gates.js:881`. The comparison adds no compile. *Basis:* source read.

**F7** — The shipping scenario `completion-requires-a-recorded-anchor` records the fingerprint of change `unrecorded` and writes it into change `recorded`. Two changes with byte-identical task text compile to different fingerprints — measured `241984884c67…` against `2a59db969a98…` — because the capsule records each authority's source path. The scenario passes today, which is direct evidence that the comparison it names never happened. *Basis:* reproduction; consistent with the shipped requirement that archiving a change moves its anchor.

**F8** — `--record` writes `keel-task-capsule/v1 sha256:<hex>` (`gates.js:239`), while `anchoredFingerprint` (`gates.js:172`) matches a bare `sha256:<hex>` anywhere in the line. Both forms are accepted today. *Basis:* source read.

**F9** — Change discovery filters the archive tree (`gates.js:58`), so no gate can select an archived change. The live-only boundary needs no new code. *Basis:* source read.

**D1** — **Drift is a hard failure, not a warning or a `needs-review`.** *Basis:* `AGENTS.md` — "drift hard-stops until explicit reauthorization returns to authoring and clears stale execution evidence" — and F2, where both surfaces that do compare already treat it as a stop. A `needs-review` would let the agent recording its own Review wave through the one condition the anchor exists to catch.

**D2** — The problem code is **`contract-drift`**. *Basis:* `keel-touch-write-guard` already calls this fact "contract drift" in prose, and the guard's own `fingerprint-drift` code is a guard-status code in a different namespace. The word the spec uses is the word the diagnostic should use.

**D3** — The refusal **names both values and the reauthorization command**, and states that evidence recorded under the previous contract is stale. *Basis:* `taskStart` already emits exactly this sentence as a re-record warning (`gates.js:263`). The refusal is the same fact discovered later; saying less than the warning would be incoherent.

**D4** — **`change-close` compares every checked task's anchor**, and refuses a checked task that records none. *Basis:* F5 plus the protocol's "that comparison holds while its change is live". A change-close that compared nothing would leave the entire post-completion window unguarded at the gate that closes the window. The missing-anchor half is included because without it the bypass is "delete the line" — but the diagnostic is written for the close context rather than reusing `task-complete`'s, whose remedy sentence ends "then complete it" and would send the reader of an already-checked task somewhere with no problem in it.

**D5** — The **`keel-task-capsule/v1` prefix stays optional**, and is used as diagnostic detail rather than gated. *Basis:* a fingerprint is a digest over the canonical serialization, so a matching value can only have come from the schema that produced it — requiring the prefix would add a second failure mode for hand-written anchors while proving nothing the comparison does not. Where it does earn its place is the drift message: when the values differ, naming the schema that compiled the current one is what tells a reader whether they are looking at contract drift or at a capsule-format change. This is issue #37's "adjacent small problem", answered rather than deferred.

**D6** — **`task-start` is untouched.** It runs before an anchor can exist and its `--record` path already warns on a changed value. *Basis:* the shipped requirement "task-start does not require an anchor" and F2.

**D7** — **One task, not two.** The comparison is one behavior reached through two call sites, and splitting by call site would be the horizontal split `keel-tdd-or-test-first` prohibits. Both call sites share one helper, one file, and one Touch set — which is precisely the identical-Touch signal proposed as a merge candidate on issue #41, evaluated here and answered "merge". Red-green discipline is not weakened: `vertical-tdd` operates per `M<n>`, and the completion checks and the close checks each have their own honest red.

## Hidden Knowledge / Assumptions

**A1** — Fixing `completion-requires-a-recorded-anchor` means recording on the change it completes, not weakening the comparison to accommodate the fixture. *Basis:* F7 — the fixture's cross-change anchor was never a valid anchor for the task it decorated. *Owner:* task 1.1, whose check asserts the repaired scenario still refuses `Contract: pending` and now also refuses a foreign fingerprint.

**A2** — `compileTaskContract` is deterministic for an unchanged live change, so a correct anchor cannot spuriously fail. *Basis:* the shipped `anchor-reverification-bound` scenario asserts a live anchor recompiles to its recorded value. *Owner:* that existing scenario, which runs in the same suite and would fail first if the assumption broke.

## Coupled Iteration Contract

Not required. No task in this change declares `Coupling: required`.

## Risks / Trade-offs

- **This makes previously-passing work fail.** Any live change whose contract was edited after recording now stops at completion. That is the defect being fixed, but it will land as a surprise in a repository mid-change. The mitigation is entirely in the message: it must name both fingerprints and the exact reauthorization command, so the reader's next action is unambiguous rather than a search.
- **A wrong comparison is worse than none.** A false drift report would block correct work at the last gate. A2 is the guard against it, and it is an existing scenario rather than a new claim.
- **The prefix decision could age.** If a `keel-task-capsule/v2` ever ships, a v1 anchor and a v2 compile will differ in value anyway, so the comparison still stops — the reader is told which schema produced the current value, and the prefix decision costs nothing at that point. Recorded here so the reasoning is available if that day comes.
