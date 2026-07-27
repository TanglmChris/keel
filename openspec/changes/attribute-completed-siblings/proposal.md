## Why

`task-complete --base HEAD` blames the selected task for the previous task's uncommitted work.

`scopeEvidence` diffs the worktree against the base and attributes every changed path outside the selected task's Touch, exempting only `keel/guard.json` and the change's own authoring directory. When the previous task in the same change has finished but has not been committed, its files are still in that diff — so they land on whoever runs next.

Issue #13 reports it from `retire-follow-up-backlog`:

```
$ keel gate task-complete --change <c> --task 1.2 --base HEAD --json
status: fail
problems:
  outside-touch: Changed path is outside Touch: AGENTS.md
  outside-touch: Changed path is outside Touch: openspec/changes/follow-up-backlog/.openspec.yaml
```

The second is real. The first is false: `AGENTS.md` was task 1.1's, and 1.1 had already passed its own completion gate.

The workaround — commit each task before starting the next — is correct and is now the documented loop. But it is an **implicit** requirement: an author who does not know it sees a scope failure naming a file they never touched, and the obvious repair is to widen a Touch that was already right. That is the opposite of what the gate is for.

Reported as issue #13 item 2, the last of that issue's three.

## What Changes

- A changed path outside the selected task's Touch is no longer attributed to it when a **completed** task in the same change declares that path in its own Touch.
- The exclusion is reported rather than silent: a warning names the path and the completed task whose Touch covers it, so an author sees that attribution was ambiguous and how it was resolved.
- Nothing else about attribution moves. An unchecked sibling's Touch grants nothing, paths no task declares still fail, and the no-base behavior is untouched.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: worktree attribution accounts for the change's own completed tasks before blaming the selected one.

## Impact

- The per-task commit convention stops being load-bearing. It stays the better habit — it keeps each task's diff reviewable — but forgetting it no longer produces a diagnostic that points at the wrong file and invites the wrong repair.
- No new state: the answer is derived from `tasks.md`, which the gate already parsed. No manifest change, no capsule change, no fingerprint change.
- Ambiguity stays visible. `--base HEAD` cannot tell who wrote a path, so where two tasks could own it the gate says so instead of silently choosing.
