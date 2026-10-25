---
description: Complete an OpenSpec task under Keel's gate — record evidence and review, then run task-complete
argument-hint: "[change] [task]"
---

Complete the task this session started. The mechanism is `keel gate task-complete`; this command only orders the steps.

## 1. Record what was run

In the task's Evidence in `tasks.md`, write each `M<n>` check's result as the command printed it, and, for a red-green strategy, its `.red` and `.green` lines. Write only what a command produced in this session; a result you did not see is not evidence.

## 2. Review

Run the `review-checklist` skill, then fill the task's Review: `Status`, `Acceptance check`, `Scope check`, and `Findings`, each finding with the disposition it actually has. Tick the task's checkbox only when Review's status is `pass`.

## 3. Run the gate

Take the change and task from the arguments: `$ARGUMENTS`, or else the task this session started.

```bash
keel gate task-complete --change <change> --task <task>
```

- `pass`: the task is complete. Report it to the owner with what changed and what was run.
- `fail` or `needs-review`: report the problem as it reads and fix the record or the work. Do not edit the task's contract to get past the gate.
