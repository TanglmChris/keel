## Why

`keel --check` reports `keel state: failed` on a `tasks.md` line that contains no commit hash. Reported in #58: the evidence prose held a fake phone number, `13800138000`, and the check answered

```
state-error openspec/changes/<change>/tasks.md:50: remove contextual commit hash from tasks.md; git log is the source of truth
```

The criterion is `TASKS_CONTEXTUAL_HASH_RE` at `scripts/install_to_repo.py:123` — a context word (`commit`, `提交`, `合入`, `master`, `main`, `HEAD`, `hash`, `哈希`) anywhere on the line, beside `\b[0-9a-f]{7,40}\b` anywhere on the line. Eleven decimal digits are eleven characters of `[0-9a-f]`, so a phone number is a commit hash to this check. Measured 2026-08-02 at 5.18.0: `提交表单时手机号 13800138000 通过校验` is refused, `时间戳 1700000000 与 commit 记录对齐` is refused, `提交订单号 20260802123 落库` is refused.

The cost is not the refusal, it is what the refusal asks for. Nothing is wrong with the line, so the only way past it is to write the evidence differently — the reporter changed the number to `138****0000` — and evidence that has been reworded to satisfy a pattern is weaker evidence than the one that was true. A state check that fails on correct work is a check people learn to route around, and then it is not protecting anything.

This is the same defect class as #60, fixed one release earlier in 5.18.0, with the repair pointing the other way. That change recorded it as `D5`: there a character class was too *narrow* and the fix was a widening; here it is too *wide* and the fix is a narrowing. The rule was right both times and the implementation of the criterion was not.

## What Changes

- A run of decimal digits alone is not a commit hash. The contextual-hash criterion requires at least one hexadecimal letter in the run, so a phone number, timestamp, order number, port, or numeric fixture is ordinary prose again.
- Nothing else about the rule moves: the context words, the scan, the message, and the four `TASKS_COMMIT_STATUS_PATTERNS` are untouched, and every run containing an `a`–`f` is still refused exactly as before.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-stateless-continuity`: the check that keeps commit state out of an active `tasks.md` is stated as a requirement for the first time, and its criterion is tied to what makes a string a commit hash rather than to how long a digit run is.

## Impact

- `scripts/install_to_repo.py`: one regular expression.
- `scripts/validate_plugin.py`: a scenario driving `keel --check` over both halves — the reported false positives are accepted, and a real hash beside a context word still fails.
- Measured across every `tasks.md` in this repository's own OpenSpec history, active and archived: 5,210 lines scanned, **zero verdicts change**. The narrowing removes no catch this project has ever made.
- Risk, stated because it is real: an abbreviated hash that happens to be all decimal digits is now missed. For a 7-character abbreviation that is `(10/16)^7` ≈ **3.7%** of them, falling to 0.6% at twelve characters and to nothing at forty. Accepted in design (D2) — a check that is wrong about correct work loses more than a check that misses one hash in twenty-seven, and the commit-*wording* patterns still catch the sentence such a hash is usually written in.
- Deliberately not changed: the strength of the context requirement, the treatment of backticked text, and the failure severity — three further repairs #58 proposes, each of which changes what the rule refuses rather than repairing how it recognizes what it already refuses. Named as non-goals in design (D3), with the residue they leave open owned by a follow-up.
- No new dependency.
