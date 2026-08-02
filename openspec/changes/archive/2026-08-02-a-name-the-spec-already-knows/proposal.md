## Why

A `Covers` reference that names a real capability but whose second segment is not a Requirement is refused with `Covers reference could not be resolved: <ref>.` and nothing else — no hierarchy, no statement of which segment failed, no use of what the spec plainly knows. The single most common way to write that reference wrong is to put the **Scenario** name in the second segment, and in that case the spec being read *contains that exact name*, one heading level down.

Reported on #49 as the 2026-08-02 supplement, where the reporter recorded the cost: two rounds. The first round removed a trailing gloss from the reference — a different shape problem, learned from the same issue's item 1 — and the error text did not change by one character. Only the second round, reading `specAuthority()` directly, found `const [capability, requirementName, scenarioName] = parts;`. The previous unattended run left this item on #49 named as the cheapest remaining one, and noted it had already consumed two reauthorization cycles.

Reproduced 2026-08-02 at 5.20.0 against a spec declaring Requirement `The store validates itself` with Scenario `A published store passes the pinned validator`:

```
Covers: demo-cap / A published store passes the pinned validator
-> Covers reference could not be resolved: demo-cap / A published store passes the pinned validator.
```

The wording this refusal needs already exists in the same function, thirty lines above, and is unreachable from here:

```
Covers reference has 4 segments; the hierarchy is capability / requirement,
or capability / requirement / scenario: <ref>
```

So the hierarchy is explained when the author writes **too many** segments and withheld when they write the right number with the wrong name in the middle. The second is both more common and harder to see, because a two-segment reference looks correct.

## What Changes

The `unresolved-covers` fallback in `specAuthority()` says which segment failed and what is there instead. Three cases, each reporting what the reader cannot see:

- The named Scenario is offered as a Requirement — the diagnostic names the Requirement that Scenario actually sits under, and spells the corrected three-segment reference.
- The capability's spec declares no Requirement by that name and no Scenario either — the diagnostic says the spec was read and holds no such name, and states the hierarchy.
- No spec declares the capability at all — the diagnostic says so, rather than implying the name inside it was the problem.

**What the gate accepts does not change.** All three cases fail before this change and fail after it, with the same `unresolved-covers` code. Only the sentence changes.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-task-capsule`: the existing requirement that `Covers` resolves durable authority gains the rule that an unresolved reference into an existing capability names which segment failed, and names the Requirement a matched Scenario belongs to.

## Impact

- `src/core/task-contract.js`: `specAuthority()`'s terminal `return` consults the candidate specs it already opened.
- `scripts/validate_plugin.py`: one scenario reproducing #49's case and asserting all three branches, plus that a resolvable reference is untouched.
- **Deliberately unchanged: `criticalAuthority()`.** #49's item 1 — a bare `D<n>` in `Covers` reported as `Missing` when design.md defines it — sits in the neighbouring function and is **not** fixed here. Reproducing it surfaced a material fact the issue did not have, recorded as Q1 in design and reported to #49: the accepted design.md shape is a line beginning with the bare token, and no design.md in this repository is written that way. Widening it changes what the gate accepts and is the owner's call.
- Risk: a diagnostic that reads more of the spec could slow compilation or throw on a malformed spec. Both bounded — the added read reuses content the same call already loaded, and runs only on the failure path, which ends in a refusal either way.
- No new dependency. No interface, protocol, timing, ordering, permission, or security boundary changes.
