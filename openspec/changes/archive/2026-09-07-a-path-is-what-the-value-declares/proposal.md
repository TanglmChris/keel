## Why

Measured across five consuming repositories — 910 task capsules, 624 path-shaped `Durable owner:`/`Resolved here:` declarations — `declaredPath()` returns something other than the declared path for **34 of them (5.4%)**, in two independent shapes.

**A sentence has no whitespace to end a path.** `openspec/FOLLOWUP.md。②本波两次重录重验` extracts whole. The extractor locates a run of non-whitespace, and Chinese prose puts no space after a path; `DECLARED_PATH_TRAILING` holds `。` but strips only what trails the run, and here the terminator sits inside it. The ASCII spelling of the same sentence works. 14 declarations.

**An illustration outranks the declaration.** `scripts/regen_baselines.py，判据见 \`tests/e2e/test_x.py\`` extracts `tests/e2e/test_x.py`. The backtick branch runs first and searches the whole value, and `Findings` is free prose where naming the owner and then citing a file is ordinary. 20 declarations, including one where the answer is the bare string `/`. This half is worse than the first: it does not refuse, it answers with the wrong file — so the gate can pass on an illustration that exists while the declared owner does not.

Both are invisible today in the repositories that carry them, which sit on Keel 5.14.0 and 5.20.0 — before the change that introduced the whitespace-run rule. They surface on upgrade.

## What Changes

- A declaration is what the value opens with. A backticked path at the start of the value wins, because that is how a path containing whitespace is declared. Otherwise the first bare run wins. A backticked span later in the value is used only when the value declares nothing else, which keeps `Durable owner: 见 \`docs/a b.md\`` working.
- A bare run ends at whitespace **or at a CJK sentence terminator** — `。，、；：！？（）【】《》「」〈〉""''`. ASCII punctuation keeps its current treatment, allowed inside the run and stripped from its end, because `a.b/c-d.e` and `f(1)/g` are paths.

## Capabilities

### Modified Capabilities
- `keel-core-gates`: the "A declared path is extracted by where it ends, not by what it is made of" requirement says a path ends at whitespace and that a backticked path is taken verbatim, without saying which of several candidates in one value is the declaration. It gains the ordering, and the sentence terminator for scripts that do not separate words with spaces.

## Impact

- Affected code: `src/core/gates.js` — `declaredPath()` only.
- Affected tests: `scripts/validate_plugin.py` — one new scenario; `a-root-file-is-a-path` and `durable-owner-vocabulary` assert the forms that must not change.
- 590 of the 624 measured declarations extract identically. The 34 that change all move from a wrong answer to the declared one.
- Direction is a correctness fix in both halves: one stops refusing a path that was written correctly, the other stops accepting a file that was never declared.
- No new dependency, no schema change, no CLI surface change.
