## Why

Two change-level sections of tasks.md — `## Invalidates` and `## Expectation Coverage` — are read by two functions in `src/core/gates.js`. Each finds its heading and then takes everything up to the next `## ` heading as the section body. In a document made of headings that is the right bound. A tasks.md is not that document: its dominant structure is a list, and what follows a change-level section is almost always a task item, not a heading.

So whenever either section is not the file's last section, it extends over the whole task list. Both halves of that fail, in opposite directions.

**It reports a problem that is not there.** With `## Expectation Coverage` above the task list and every entry closed, `keel gate change-close` refuses:

```
Problem: E1 lacks behavior coverage, durable owner, or discard rationale. …
Problem: E2 lacks behavior coverage, durable owner, or discard rationale. …
```

`E1` is closed by `Covered by: 1.1` three lines above. The entries the gate actually judged are the `- E1:` lines each task declares under its own `Covers`, swept in when the section swallowed the tasks. Moving the identical section to the end of the file makes the same command pass with no edit to its content.

**And it stays silent about a problem that is there.** The section's `- None.` early return matches anywhere in the swallowed text. A `repo-action` task declares `Touch:` as a bare `- none`, so with `## Invalidates` above the task list, an `I1` that closes nothing at all passes `keel gate task-start` — the whole declaration read as "this change invalidates nothing".

The position that avoids all of this is written down nowhere. Not in `AGENTS.md`, not in either shipped template, not in the schema, not in any diagnostic. It is uniform across the archive only because it is a habit. An author who follows the error message instead of the habit is sent to an `E<n>` that has nothing wrong with it, and an unattended run sent there will spend a cycle repairing something that was already correct — or "repair" it into a shape that quiets the gate and is worse.

The repository has already met this defect from the other side. When a change-level section sat *after* the last task, its lines were appended to whichever field was open last — the `Evidence`, in every shipped template — and a token quoted in the section made that Evidence non-concrete. The fix ended a task's body at the next task **or** the next heading, and shipped as a requirement that also says every consumer of a task's extent must use that one boundary. The section readers were never brought along. They hold the mirror half.

Reported as #71, from a fresh change rather than from the archive: the archive cannot hold this defect, because it only stores what passed.

## What Changes

- A change-level section ends at the next `##` heading **or at the next task**, whichever comes first. Its extent becomes the section the author wrote, wherever in the file it sits.
- Both readers compute that extent through one shared function rather than through two identical copies.
- The task half of the boundary is the task list `parseTasks()` already returned, not a second checkbox pattern that would have to keep agreeing with it.
- Section position stops affecting any verdict. It is not documented and not required — it is made irrelevant.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-task-capsule`: the extent of a change-level section of tasks.md, the mirror of the boundary already published for a task's own body.

## Impact

- `src/core/gates.js` — one new helper, and the two duplicated slice lines it replaces.
- `scripts/validate_plugin.py` — a scenario asserting both sections in both positions, closed and unclosed.
- `keel gate change-close` and `keel gate task-start` verdicts, for a tasks.md whose section is not last. No diagnostic code and no message text changes; what changes is which entries are judged.
- No change to what closes an entry — `Covered by:`, `Updated by:`, `Durable owner:`, `Discard reason:` are untouched — and no change to the entry patterns themselves.
- No change to the tail position, which is the shape every archived change uses and which this change asserts rather than assumes.
