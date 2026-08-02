## Why

A compact v4 task whose `Evidence` carries a bare angle bracket is refused by `keel gate task-complete`, and the *first* problem it reports names `Commands` — a field the compact schema does not have. Reported in #52, where the cost was about twenty minutes spent auditing the `Verify` block, counting `M<n>` checks, and diffing against tasks that had already passed, before reading `gates.js` to find the actual link.

Reproduced 2026-08-02 at 5.19.0. An `Evidence` line reading `M1: pass —— 最大照亮比例 0.001916（判据 <0.02），最小照亮比例 0.998107（判据 >0.98）。` produces:

```
Problem: Commands must define at least one M<n>.
Problem: Evidence must be concrete.
```

Neither mentions an angle bracket. The first names another schema's field, and it sorts first, so it is the one an author acts on.

Two independent defects produce that pair:

- `missingFieldProblems()` (`src/core/task-contract.js:416`) emits a bare `${name} must be concrete.` while `unfilledToken()` sits eight lines above it in the same file. That function's own comment states it exists to "explain a non-concrete field instead of letting the caller infer a different schema from it" — and this is the caller that infers one.
- When the contract carries any diagnostic, `gates.js:851` discards the whole compiled contract, and `completionChecks()` falls back to `commandLabels()`, which reads `field(task, "Commands")`. For a compact task that field is always absent, so `missing-commands` fires as a pure artifact of the fallback rather than as a fact about the task.

The rule this change applies is already shipped: `keel-task-capsule` requires that a non-concrete `M<n>` check name the token that made it non-concrete, and `task-contract.js:254-268` implements exactly that. It was applied to checks and not to the required fields beside them.

## What Changes

- A required field judged non-concrete because of an unfilled token names that token, and says the token can be fenced in inline code when it is literal text rather than a slot. Same wording shape as the `M<n>` diagnostic that already does this.
- When the contract could not be compiled, `task-complete` no longer asserts anything about the verification form. The compiler's own diagnostics already say what is wrong; the fallback's answer is about a field the author may never have declared.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-task-capsule`: the existing requirement that a non-concrete `M<n>` check names its token is generalized to the required fields validated beside it, so `Covers`, `Verify`, `Evidence`, and `Commands` answer the same way.
- `keel-core-gates`: states that a gate whose contract failed to compile reports the compilation diagnostics and does not derive a second problem from a schema fallback.

## Impact

- `src/core/task-contract.js`: `missingFieldProblems()` consults `unfilledToken()`.
- `src/core/gates.js`: `completionChecks()` suppresses the derived `missing-commands` problem when no contract compiled.
- `scripts/validate_plugin.py`: one scenario reproducing #52's reported pair and asserting both halves.
- **Deliberately unchanged: `UNFILLED_TOKEN` is not widened.** #52's second suggestion is to narrow `<[^>]+>` so prose like `（判据 <0.02）` stops matching. That would change what the gate *accepts*, and it contradicts a decision this repository already recorded — `keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md` answers the same question with "a token left bare in the text is still reported", with the backtick as the deliberate escape. Named as a non-goal in design; left with the owner and recorded on #52.
- Risk: suppressing a problem could turn a failing gate into a passing one. It cannot here — `gates.js:853` pushes the compiler's diagnostics unconditionally, and the suppression applies only when those diagnostics are non-empty. Asserted by the scenario rather than argued.
- No new dependency. No interface, protocol, timing, ordering, permission, or security boundary changes.
