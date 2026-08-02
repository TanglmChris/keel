## Context

`keel --check` runs a set of semantic checks over every active `tasks.md`. They exist to keep one thing out of that file: state that git already owns. A commit hash pasted into a task, a `已合入 master`, a manually maintained completion count — each makes `tasks.md` a second, staler copy of something derivable, and the rule that forbids them is right.

Recognizing a *pasted hash inside a sentence* is the hard half. The line is free prose, so the check cannot read a field; it looks for a context word and a hash-shaped token on the same line. "Hash-shaped" was written as `[0-9a-f]{7,40}` — a class that answers *what characters may a hash contain* and is then used to answer *is this token a hash*. Every decimal number of seven to forty digits satisfies it.

## Goals / Non-Goals

**Goals:**
- Evidence prose containing an ordinary number is not refused as a commit hash.
- A pasted commit hash beside a context word is still refused, with the same message.
- The residual miss the narrowing creates is measured and stated rather than assumed small.

**Non-Goals:**
- Strengthening the context requirement — #58's first suggestion, requiring the surrounding text to *look like* a hash reference. It would fix more than this change does, and it changes which lines the rule refuses, which is a decision about the rule rather than about the criterion (D3).
- Exempting backticked text — #58's third suggestion. `task-contract.js` does strip inline code before looking for an unfilled token, so the shape exists in this repository, but there it protects prose that must *name* a pattern. Here it would exempt the most common way a real hash is written, which is a weakening of the rule and not a repair of the criterion (D3).
- Downgrading the failure to a warning — #58's fourth suggestion. That is a change to what `keel state: failed` means, and it repairs a false positive by making every true positive quieter (D3).
- Widening what counts as a hash. The same 5.18.0 change that fixed the opposite defect recorded that neither direction is a general answer.

## Decisions

- **F1** — the criterion is `TASKS_CONTEXTUAL_HASH_RE` at `scripts/install_to_repo.py:123`: a context word from `commit|提交|合入|master|main|HEAD|hash|哈希` and `\b[0-9a-f]{7,40}\b` in either order on one line, applied per line at `:681` to every non-rule line of every active `tasks.md`. *Basis: reading the file at 5.18.0.*
- **F2** — three shapes fail, measured 2026-08-02 at 5.18.0 by running the expression directly: `提交表单时手机号 13800138000 通过校验`, `时间戳 1700000000 与 commit 记录对齐`, and `提交订单号 20260802123 落库` are each reported as a contextual commit hash. #58 reports the first; the other two are the same token class with the other two context words that make it likely — a timestamp and an order number both sit naturally beside 提交. *Basis: direct execution against the compiled pattern.*
- **F3** — the existing coverage of this rule is the `cli` scenario, which asserts the failure on `合入 master(a4ca804)`. That token contains `a` and `c`, so it is unaffected by the narrowing and stands as the regression this change must not break. *Basis: `scripts/validate_plugin.py`, the `status-drift` fixture.*
- **D1** — a hash-shaped token must contain at least one of `a`–`f`. This is the property that distinguishes a hexadecimal identifier from a number a person wrote: base-16 is the only reason `a`–`f` appear at all, and a decimal-only run is evidence of nothing. The implementation keeps the existing length and word-boundary conditions in a lookahead and requires the letter in the body, so the token that matches is still exactly the token that matched before, minus the all-decimal ones. *Basis: F2 — every measured false positive is all-decimal, and every true positive in F3 is not.*
- **D2** — the residual miss is accepted and quantified. A genuine abbreviated hash containing no `a`–`f` is now missed: `(10/16)^7` ≈ 3.7% of 7-character abbreviations, 0.6% at twelve, ~1 in 10⁹ at forty. Two things bound it. Measured across every `tasks.md` in this repository's OpenSpec history, active and archived — 5,210 lines — **no verdict changes**, so the class is not one this project actually produces. And `TASKS_COMMIT_STATUS_PATTERNS` is untouched, so `commit hash`, `已提交`, `合入 master`, and `merged into main` still fail on the wording regardless of the digits. *Basis: direct measurement over `openspec/**/tasks.md` at 5.18.0.*
- **D3** — the other three repairs #58 proposes are out of scope, and the distinction is which question they answer. This change repairs *how the check recognizes a commit hash*, which the repository can decide alone: a commit hash is hexadecimal, and that fact is not a matter of policy. The other three change *which lines the rule refuses* — how much context is required, whether quoted text is exempt, and whether a violation stops `--check` at all. Those are the owner's to decide, and the residue is real: a hex-shaped third-party identifier such as `68c02ce6`, which #58 also reports, is still refused by this change. It carries a durable owner rather than being folded in. *Basis: #58's own ordering, which lists them as four independent options at descending precision.*

## Hidden Knowledge / Assumptions

- **A1** — the numbers that appear in evidence prose are decimal. Phone numbers, timestamps, order numbers, ports, and counts are the cases #58 names, and all are base-10. A hexadecimal literal in evidence — `0xdeadbeef`, which #58 mentions in passing — is still refused when a context word shares its line, and this change does not address it. *Basis: F2. Owner: the follow-up in D3, which carries every hex-shaped non-hash case together rather than splitting them across changes.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- The narrowing could be read as licence to relax any over-matching pattern by shrinking its character class. It is not: what makes this repair correct is that the removed characters carry no evidence of the thing being detected, which was established by measuring the false positives, not by preferring fewer refusals.
- One regular expression now carries a lookahead, which is harder to read than the class it replaces. Mitigated by keeping the length and boundary conditions verbatim inside it, so the diff shows exactly one added condition.

## Open Questions

None.
