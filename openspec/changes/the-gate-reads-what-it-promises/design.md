# Design

## Verified facts

- **F1** — `parseTasks` at `src/core/task-contract.js:70-73` sets each task's body to `lines.slice(task.line, end)` where `end` is the next task's line or `lines.length`. Nothing stops at a `##` heading. The field loop at `:76-84` appends any non-field line to the currently open field, so trailing sections land in whichever field was last declared — in the shipped template, `Evidence`.
- **F2** — The same absorption applies to a `## <group>` heading between task groups: it is appended to the previous task's last field. Milder only because a group heading rarely carries an unfilled-slot token.
- **F3** — `contractAnchorPlan` at `src/core/gates.js:132` recomputes the extent itself from `selection.tasks[index + 1].line`, so it inherits F1 independently: for the last task, its `- Contract:` search runs to end of file and can match a line inside a trailing section.
- **F4** — `anchoredFingerprint` at `src/core/gates.js:154` matches `sha-?256[\s:`]*([a-f0-9]{64})` and returns null otherwise. `completionChecks` never asks for one, so a `pending` anchor is not compared and not reported. Confirmed by fixture: a task with `Contract: pending` and complete Evidence/Review passes `task-complete` with zero problems.
- **F5** — All three tasks in the shipped `keel-spec-driven` tasks template emit `- Contract: pending`, so a template-derived task always carries the line.
- **F6** — `AGENTS.md` already states the recording step as part of the loop: "record the fingerprint in the task's Evidence `Contract` line before implementation, and resume, projection, and completion recompile and compare it". `assets/bootstrap/AGENTS.md` states the same in one line. The behavior change makes the shipped prose true rather than aspirational.
- **F7** — `invalidation-phrase` at `src/core/gates.js` requires `/"[^"\n]{3,}"/` in each `I<n>` entry; `isConcrete` rejects `UNFILLED_TOKEN` outside inline code. Backticking the phrase fails the first, double-quoting it fails the second once the section is read as Evidence.

## Decisions

### D1 — A task body ends at the next task or the next `##` heading

Cap each task's extent at the first line matching `^\s*##\s` after its own line. A `##` heading is by construction not part of a task: task fields are `  - Name:` lines, and every heading in a tasks.md is either a group heading or a change-level section.

This fixes F7's contradiction as a consequence rather than as a special case — once the section is no longer read as Evidence, its double-quoted phrase is never subjected to the concreteness test, so both checks can be satisfied by the same text. That is the reason to fix the extent rather than to relax either check: the checks were never in conflict, the parser only made them appear so.

`contractAnchorPlan` reads the same extent (F3), so the parsed task carries it and gates consumes it instead of recomputing.

Rejected: stopping only at the two known section headings (`## Invalidates`, `## Expectation Coverage`). That fixes today's two names and leaves the next change-level section to rediscover the bug — and it would still leak group headings (F2).

### D2 — A recorded anchor is a precondition of completion

`task-complete` reports a problem when the selected task's `Contract` anchor holds no compiled fingerprint, naming `task-start --record`. This is the hard-refusal option, chosen by the user over a `needs-review` signal and over exempting hand-written tasks that omit the line.

The reasoning: the value of the anchor is that drift hard-stops, and a task that never recorded one has no drift detection at all while presenting as fully gated. A `needs-review` result would surface it, but the result of "surfaced and then completed anyway" is the same unprotected task. F6 means this is enforcing documented workflow, not inventing a requirement.

Cost, stated plainly: every repo using Keel must run `task-start --record` before `task-complete`. That step is currently optional. The refusal names the command, and `--record` is idempotent — it rewrites the anchor in place — so the recovery is one command with no manual edit.

This applies to an explicitly named task as well as an inferred one. 5.3.7 closed the inference path with `ambiguous-completion-selection`; that diagnostic stays for the selection case, and the new one covers the task the caller named.

### D3 — The two checks report separately

Selection ambiguity and a missing anchor are different problems with different fixes — one needs `--task`, the other needs `--record` — so they keep distinct codes. The 5.3.7 selection refusal already names both commands because at that point either could be the caller's intent; once a task is named, only the anchor is at issue.

## Risks

- **R1** — D1 changes what every task's `Evidence` field contains for the last task of every change, which could move a compiled fingerprint. Mitigated by measuring: the capsule does not carry Evidence, so the fingerprint should be unchanged. Asserted rather than assumed, because a silent fingerprint move would drift every live change in every consumer repo at once.
- **R2** — D2 turns a passing path into a failing one for any repo that does not use `--record`. Accepted by explicit decision, and called out in the release notes as the upgrade note. The refusal names the exact command.
- **R3** — D1 could truncate a task that legitimately contains a `##` line, for example inside a fenced code block in a field value. Judged not worth handling: no field in the shipped template or in this repository's history carries one, and the alternative is a Markdown-aware parser in a gate that must stay deterministic and cheap.

## Questions

- None.
