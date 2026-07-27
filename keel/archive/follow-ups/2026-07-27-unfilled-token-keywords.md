# The unfilled-token test also matches bare keywords in prose

Date: 2026-07-27. Owner task: openspec/changes/diagnostics-must-not-mislead/tasks.md#1.1.

## Finding

`UNFILLED_TOKEN` in `src/core/task-contract.js` is:

```js
/(<[^>]+>|\bTODO\b|\bTBD\b|\bplaceholder\b)/i
```

Issue #7 reported the angle-bracket half. The other half is just as reachable: the bare words `TODO`, `TBD`, and `placeholder` match case-insensitively anywhere in a field, so ordinary prose *about* unfilled tokens is judged unfilled.

This change hit it three times while being authored:

1. Task 1.1's `Verify` first read "a compact v4 task whose Verify carries a placeholder token". `keel gate task-start` returned eleven problems — the nine expanded v3 `missing-field` entries plus `missing-boundary` and `missing-command-check` — none mentioning the word `placeholder` that caused it.
2. A `Covers` entry referencing this change's own spec scenario, then named "Placeholder-judged Verify is reported, not silently downgraded", made `Covers` non-concrete for the same reason. `Covers` is required in both the compact and expanded sets, so the reference was unusable.

3. Task 1.1's own `Evidence` block, written *after* the fix landed, could not be recorded: `Evidence` is itself guarded by the concreteness test, and the evidence text quoted the matched tokens it was describing. `keel gate task-start` returned `missing-field: Evidence must be concrete.`

All three were resolved by rewording — the scenario was renamed to "Non-concrete Verify is reported, not silently downgraded", and the evidence now describes the tokens instead of quoting them — which is precisely the workaround cost issue #7 describes.

The third instance is the sharpest: **a task cannot record evidence about the concreteness test without tripping it.** Any future work on this pattern will hit the same wall.

## What was fixed, and what was not

Task 1.1 of this change makes the failure *legible*: a declared-but-unfilled `Verify` now produces one `non-concrete-verify` diagnostic naming the matched token, instead of silently selecting the expanded v3 field set. That covers the keyword case too — the diagnostic names `placeholder` just as it names `<date>`, and its text says the bare keywords read as unfilled including inside prose.

Task 1.2 narrows the rule for **all four token forms**, not only angle brackets: the concreteness test now strips inline code spans before looking for a token, and does so *after* the empty/none/pending test so a field whose whole value is one code span is not misread as empty.

**Resolved.** The question this note originally left open — whether the bare keywords deserved the same exemption as angle brackets — was answered yes, and task 1.2 shipped it that way. The deciding argument was the third instance above: an author is far more likely to write these words *about* unfilled slots than to leave one unfilled inside backticks, and the backtick is a deliberate act. The narrower rule still stands where it matters, because a token left bare in the text is still reported.

Effect on the three instances: all three would now be non-events. Evidence blocks can quote the token forms directly, provided they are fenced — this note does so throughout, and the evidence recorded on tasks 1.1 and 1.2 does too.

The remaining false-negative surface is a genuinely unfilled slot someone wrote inside backticks, e.g. a `Touch` entry of `` `<path>` ``. Risk A1 in the change design accepts it: the Touch-path checks still reject a path that does not exist, so the slot fails later on a check that names the path rather than the token.

Deliberately not a separate GitHub issue: issue #7 already owns this family and task 1.2 closes this part of it.
