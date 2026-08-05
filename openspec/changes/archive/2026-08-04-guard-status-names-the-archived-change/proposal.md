## Why

`keel guard status` has one answer for two different states, and for one of them every word of that answer is unusable.

A manifest whose change directory has been archived, and a manifest whose task id simply is not in a live `tasks.md`, both reach the same branch of `guardStatus()` and produce byte-identical output at 5.26.0:

```
Status: drifted
Selection: demo#1.1
Problem: Guarded task demo#1.1 no longer resolves; reauthorize through `keel gate task-start` and `keel guard start`.
```

For the second state that instruction is right. For the first it names two commands that cannot work, and measuring them says so:

```
$ keel gate task-start --change demo --task 1.1
keel: gate input error: missing OpenSpec tasks file: …/openspec/changes/demo/tasks.md
$ keel guard start --change demo --task 1.1
keel: guard input error: task demo#1.1 does not exist
```

The one action that resolves it — `keel guard clear` — is named by none of the three.

This is the second surface of a repair the repository already made. 5.12.0 taught the PreToolUse write guard to separate a change directory that is *gone* — a fact — from a task id it merely cannot match inside a live `tasks.md` — a parse miss it must not guess about. That fix landed in the hook and stopped there. The published requirement is scoped to "the write guard", and the design that shipped it recorded `keel guard status` as already classifying the state correctly, which is how the twin surface came to be skipped: status does report `drifted`, which is the right *word*, above advice that cannot be followed.

The timing is the worst available. This state is reachable only immediately after `openspec archive`, which is to say at the first write of the next change — so a session that closes two changes meets it twice, each time at the moment it has just started something new.

Reported as #56. Its first half was fixed in 5.12.0; this is the half that was left, confirmed still present at 5.26.0.

## What Changes

- `keel guard status` distinguishes a manifest whose change directory no longer exists from one whose task id is absent from a live `tasks.md`, testing the same object the hook tests.
- The first reports the manifest as stale, names `openspec/changes/<change>` as the thing that is gone, and names `keel guard clear` as the action.
- The second is untouched — same code, same message, same status.
- The two states become distinguishable by problem code, so a `--json` reader does not have to parse prose to tell them apart.
- Failing closed does not change, and neither does the `drifted` status word. What changes is what the surface says.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-touch-write-guard` — the requirement that separates a vanished change from a parse miss stops being scoped to the write guard hook and covers every surface that reports the manifest's state.

## Impact

- `src/core/guard.js` — `guardStatus()` gains the directory test the hook already performs.
- `openspec/specs/keel-touch-write-guard/spec.md` — one requirement broadened, two scenarios added.
- `scripts/validate_plugin.py` — one new scenario driving the shipped CLI on scratch repositories in both states.
- No change to the manifest schema, to any status word, to `keel guard start`, to `keel gate task-start`, or to whether any write is allowed.
