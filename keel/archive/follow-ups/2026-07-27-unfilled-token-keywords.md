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

Task 1.2 narrows only the angle-bracket case, exempting angle brackets inside inline code spans.

**Deferred:** whether the bare keywords should also be narrowed — for example by exempting them inside inline code spans, or by requiring them to stand alone as a whole field value. Arguments both ways:

- For narrowing: a task legitimately describing placeholder handling, TODO scanning, or TBD conventions cannot write those words in prose. Keel's own change here is the existence proof.
- Against narrowing: the keywords exist to catch a template the author forgot to fill, and an author writing `TODO` in a `Verify` check is more often unfinished than descriptive. Narrowing trades a false positive for a false negative in a gate whose purpose is refusing unfinished authority.

The diagnostic from task 1.1 lowers the cost — the author is now told which token to change instead of being handed the wrong schema — but three hits inside one change is not a hypothetical. The recommended narrowing is to exempt all four token forms inside inline code spans, which is what task 1.2 does for the angle-bracket form; extending the same exemption to the three keywords would have made every one of the three instances above a non-event, because each wrote the keyword as prose rather than as an unfilled slot.

Deliberately not a separate GitHub issue: issue #7 already owns this family, and task 1.2 is the natural place to widen the exemption. If task 1.2 ships angle-brackets-only, attach this note to issue #7 as the argument for the rest.
