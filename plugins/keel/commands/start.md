---
description: Start an OpenSpec task under Keel's gate — compile its capsule, record the fingerprint, arm the write guard
argument-hint: "[change] [task]"
---

Start one task of an approved OpenSpec change. The mechanism is `keel gate task-start`; this command only orders the steps.

## 1. Choose the task

Take the change and task from the arguments: `$ARGUMENTS`. With none given, run `keel context` and use the task it selects. When it selects none, or names one you did not expect, stop and ask the owner which task to start.

## 2. Run the gate

```bash
keel gate task-start --change <change> --task <task>
```

- `pass`: copy the printed fingerprint into the task's Evidence `Contract:` line in `tasks.md`, as `keel-task-capsule/v1 sha256:<digest> (keel <version>)`. On Claude the gate has also armed the write guard over the task's `Touch` paths.
- `fail`: report the `Problem:` line as it reads. The task's contract needs authoring before it can start; do not edit around the gate.

## 3. Before writing any product file

Read the task's `Read` list, then follow its `Verify` strategy. A red-green strategy writes the failing check first.
