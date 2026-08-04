## Why

`keel --check` scans every active `tasks.md` for state that git already owns. Two of its rules read free prose, and both of them are currently reading text that was never a claim about commit state.

**A context word is matched as a substring.** `TASKS_CONTEXTUAL_HASH_RE` pairs a hash-shaped token with a context word from `commit|提交|合入|master|main|HEAD|hash|哈希`, and none of the ASCII alternatives carries a word boundary. So `remaining` supplies `main`, `heading` supplies `head`, `domain` supplies `main`, and `maintains` supplies `main`. A line that mentions a contract fingerprint beside the word `remaining` is refused as a recorded commit hash:

```
state-error openspec/changes/demo/tasks.md:18: remove contextual commit hash
from tasks.md; git log is the source of truth
```

Measured over this repository's own 53 `tasks.md`: 12 lines are refused, and **4 of them are this** — `remaining` twice and `heading` twice. Every hex token on those four lines is a `sha256:` contract anchor or a recompiled fingerprint. Not one is a commit identifier.

**A `Covers:` reference is read as a claim.** A Covers entry is not prose; it is a citation whose three segments must resolve to names that exist in a spec, and one that does not resolve is already refused as `unresolved-covers`. But the wording rules read it as a sentence. Cite `keel-core-gates / Dirty-worktree attribution is conservative / …` — a requirement published in this repository today — and `keel --check` reports:

```
state-error …/tasks.md:11: remove dirty/uncommitted state from tasks.md; keep
durable work state in OpenSpec and use HANDOFF only as an explicit pointer
override
```

The author has recorded no dirty state. They have named a requirement about it. The only way past the refusal is to rename the requirement, which is what #65 documents happening: a requirement had to be called "A recorded commit **identifier** is recognized by what makes it one" because calling it a commit hash made every task that cited it fail. **11 lines across 4 changes in this repository's history sit in this shape**, and 8 of them name a published requirement. Those rules have been in the file since the initial commit, so each of those lines was a live `state-error` for as long as its change was active.

Both are the same defect wearing different clothes: the check matches text that is not the assertion it is looking for. #58 already established what this costs — not the refusal, but that nothing is wrong with the line, so the only way past it is to reword something that was true. A check that refuses correct work is one people learn to route around, and by then it is not protecting anything.

The material choice here was the owner's and is already made. #65 records it: word boundaries in the form that keeps inflections (`committed`, `commits`, `hashes`) rather than the stricter form that would drop them, and the `Covers:` exemption handled separately from the backtick question, which stays declined.

## What Changes

- The ASCII context words carry word boundaries and their inflected forms: `commits?|committed|committing|master|main|HEAD|hash(es)?`. A word inside another word no longer supplies the context.
- The Chinese context words stay unbounded, because `\b` cannot bound them — every character of `提交` is a word character, so `\b提交\b` fails on `已提交` and `未提交`, which are exactly the true positives the rule exists for.
- A `Covers` field is exempt from both prose rules. The exempt region is the field as the contract compiler bounds it: the `- Covers:` label line and every line under it up to the next field label.
- Nothing else from #65 moves. Exempting backticked text and downgrading the failure to a warning were recorded as the owner's decisions in 5.19.0's design D3 and remain declined; this change adds no new fact about either.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-stateless-continuity`: which lines of an active `tasks.md` the project-state check refuses — a context word must be a word, and a Covers citation is not a record.

## Impact

- `scripts/install_to_repo.py` — `_HASH_CONTEXT_WORD` gains boundaries and inflections; a Covers-field bound is computed per file and skipped by both rules.
- `scripts/validate_plugin.py` — one scenario driving both directions through `keel --check`.
- `keel --check` verdicts. Over this repository's whole OpenSpec history: contextual-hash refusals fall from 12 lines to 8, no line is newly refused, and the 11 wording refusals inside Covers fields become 0. Every true positive in the corpus survives — `合入 master(a4ca804)`, `committed <hash>`, `已提交` — verified line by line rather than assumed.
- Residue, stated rather than left to be discovered: a genuine commit hash pasted into a Covers entry is no longer refused by this check. It is bounded by `unresolved-covers`, which refuses any Covers entry that does not resolve to a spec name or a design reference, so the hash would have to be part of a name that exists in a spec.
