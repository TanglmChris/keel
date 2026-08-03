## Why

`## Expectation Coverage` and `## Invalidates` are read to the next `## ` heading. In a tasks.md there usually is no next heading — what follows a change-level section is the task list, and a task is `- [ ] 1.1 …`, not a heading. So a section placed anywhere but the file's tail swallows every task body after it, and the two checks that read it then read the tasks.

Reported on #71, reproduced 2026-08-02 at 5.21.0 in a scratch repository. The same tasks.md, one section moved and not one character of content changed:

```
## Expectation Coverage last in the file   -> change-close: pass
the same section above the task list       -> change-close: fail
   E1 lacks behavior coverage, durable owner, or discard rationale.
```

`E1` is closed by `Covered by: 1.1` three lines above the refusal. What the gate actually found was the `- E1: public behavior` line a task declares under its own `Covers`, which the widened section absorbed and the entry pattern — `^\s*-\s+(E\d+)`, any indentation — read as a second, unclosed E1.

The same slicing has a second mode, and it is the worse one. Reproduced in the same repository: with the section above the task list and a task declaring

```
  - Touch:
    - none
```

— the shape a `repo-action` task's `Touch` is required to take — an `E1` with **no closure at all** returns `pass`. The `- None.` early return matched a line inside a task body, so the whole declaration was skipped without a word. One archived tasks.md in this repository already carries that `- none` line.

The position that avoids all of this is written nowhere: not in `AGENTS.md`, not in the shipped template, not in either diagnostic. It is a habit, uniform across 21 of 21 archived changes and never stated. An author who puts the section where it reads best is told to fix an `E<n>` that is already correct — or is told nothing at all.

## What Changes

A change-level section ends at the next `## ` heading **or at the next task**, whichever comes first. That is not a new rule: `parseTasks()` already ends a *task's body* at the next task or the next heading, and `keel-task-capsule / A task body ends at the next task or the next heading` already requires that "Every consumer of a task's extent MUST use that same boundary rather than recomputing one." The section readers recompute one, and implement only the heading half of it. This change makes the two halves one shared helper.

Both readers are fixed, not only the reported one. They are the same two characters-identical lines in `invalidationProblems()` and `expectationProblems()`, and the spec this change extends already names repairing one reader and leaving the others as how a fixed defect reappears.

**Section position stops mattering, rather than becoming a documented requirement.** #71 offers both endings — write the rule down, or cancel it. Cancelling is the repair; requiring a position would newly refuse a layout nothing has ever called wrong, and would need a new diagnostic to say so honestly.

**One shape that passes today will fail after this change**, and that is the point of it: an unclosed `E<n>` or `I<n>` in a section that a task's `- none` line had been silently closing. No archived change is affected — all 21 put both sections in the tail, where the slicing is unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-task-capsule`: the existing requirement that a task body ends at the next task or the next heading gains its mirror — a change-level section ends at the next heading or the next task — and the rule that both boundaries are one shared computation.

## Impact

- `src/core/gates.js`: one `sectionBody()` helper replaces the duplicated slice in `invalidationProblems()` and `expectationProblems()`. Both already receive the parsed task array, so the boundary needs no new parse and no second checkbox pattern.
- `scripts/validate_plugin.py`: one scenario driving both sections through `keel gate change-close` and `keel gate task-start` at both positions, asserting the closed case passes, the unclosed case is refused, and the tail position is unchanged.
- Risk: a suite scenario that passes today only because a section absorbed the task list is asserting something untrue and will surface as a failure. That is a correct outcome; the fix is the assertion, not the boundary.
- No new dependency. No diagnostic code or message text changes. No interface, protocol, timing, ordering, permission, or security boundary changes.
