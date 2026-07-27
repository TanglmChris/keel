## Why

Keel's own drift diagnostics tell an author to reauthorize, and then the tool refuses to let them.

When a guarded task's authority changes — a Touch path was under-declared, a Verify check was tightened — `keel guard status` fails with `fingerprint-drift` and says: "reauthorize through `keel gate task-start` and `keel guard start`". Doing exactly that with `--record` fails:

```
"code": "record-refused",
"message": "--record requires the selected task's Evidence to contain the literal line
            \"- Contract: pending\"; the anchor is already recorded or missing,
            so nothing was written."
```

The author must first hand-edit `tasks.md`, replacing the recorded `- Contract: keel-task-capsule/v1 sha256:…` line with the literal `- Contract: pending`, before the gate will write the new fingerprint. In the 2026-07-27 dogfood session (two changes, nine tasks) that manual step was performed **five times**. It is also the riskiest step in the loop: it is a hand edit of one fingerprint line in a file that holds one such line per task, and editing the wrong one silently revokes another task's authorization without any gate noticing.

The refusal was written to protect the recorded start evidence that drift detection depends on. It does not: the manual edit it forces rewrites exactly the same line the gate would have written, and clears no execution evidence either. The refusal buys no safety — only cost, on the one path Keel itself tells authors to take.

Reported as issue #13 item 1.

## What Changes

Make recording the current fingerprint an idempotent operation instead of a once-only one.

- `--record` replaces the selected task's `- Contract:` Evidence anchor whatever its current value, instead of only the literal `pending` form.
- `--record` refuses only when the selected task has no `- Contract:` line at all — a genuinely malformed capsule, not a normal reauthorization.
- The result distinguishes the three outcomes: `recorded` (the anchor was `pending`), `rerecorded` (a different value was replaced), and `unchanged` (the anchor already carries this exact fingerprint, so nothing is written).
- A re-record that lands a *different* fingerprint emits a warning naming the previous one, because execution evidence produced under the previous contract is now stale. That is the real risk the old refusal gestured at and never enforced.

Out of scope: issue #13 items 2 (`task-complete --base HEAD` attributing the previous task's uncommitted work) and 3 (a `--doctor` hint that gate code must be run through `node bin/keel.js` when developing Keel itself). Both stay open on #13.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: the explicit `--record` anchor write becomes idempotent over any recorded value, refusing only a missing anchor, and reports which of the three outcomes occurred.

## Impact

- The documented recovery path — update task authority, reauthorize, re-verify — runs without a manual file edit.
- The most error-prone step in that loop, hand-editing one fingerprint line among many, is removed.
- A contract change made during reauthorization becomes visible at the moment it happens, instead of being implied by a refusal whose message named the anchor form rather than the risk.
- Gate write-boundedness is preserved and slightly tightened: a no-op re-record now writes nothing at all.
- No change to compiled capsules or fingerprints; `task-start` without `--record` stays byte-identical.
