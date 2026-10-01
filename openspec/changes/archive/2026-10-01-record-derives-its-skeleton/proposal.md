## Why

Issue #179 asks Keel to cut mechanical bookkeeping the CLI can derive, while keeping every check that can falsify a model's judgment. The costliest such step today: before `task-start --record` will run, an author must hand-write `- Contract: pending` and one `- M<n>: pending` line per check, plus the `.red`/`.green`, Review, Blocker, and Reauthorizations slots the strategy will later demand. All of it follows from the compiled capsule. A task missing any of these lines is refused with `evidence-label-mismatch` or `record-refused`, even though nothing about its contract is wrong.

## What Changes

- `task-start --record` fills the selected task's missing record slots from its compiled capsule before anchoring: `Contract`, each bare `M<n>`, `.red`/`.green` for red-green checks not tagged `(regression)`, `.detects` where a check declares `Detects:`, a Review block with its four fields, `Blocker: none`, and `Reauthorizations: none`. It writes only absent slots, inside the selected task's Evidence, overwrites nothing, and a second run writes nothing. It never fills a result, a Review verdict, or a keep reason, and never touches Covers, Touch, Verify, or Acceptance. A capsule with any authoring error is still refused and nothing is written.
- Without `--record`, the gate is unchanged; a refusal for missing record slots now says that `--record` would fill them.
- `keel-review-checklist` drops two bullets that restate checks `task-complete` already refuses mechanically: the Contract anchor and drift, and `.red`/`.green` presence. It keeps the judgment the gate cannot make, which is whether the evidence proves the behavior.
- The re-record recovery message already distinguishes checks declared kept from those still stale, and already says Keel does not verify that declaration (#104, #112). It is left as it is.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-core-gates`: `--record` derives missing record slots instead of refusing a task with no `Contract` line.
- `keel-expectation-slice-evidence-gates`: the review checklist no longer restates mechanically enforced evidence shape.

## Impact

`src/core/gates.js`, `scripts/validate_plugin.py`, both copies of `keel-review-checklist/SKILL.md`, the specs above, and the changelog. No new dependency; no gate is weakened, because every slot written reads `pending` and `task-complete` still refuses `pending`.
