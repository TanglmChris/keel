---
name: "OPSX: Apply"
description: Implement tasks from an OpenSpec change (Experimental)
allowed-tools: Bash(openspec:*)
category: Workflow
tags: [workflow, artifacts, experimental]
---

Implement tasks from an OpenSpec change.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name (e.g., `/opsx:apply add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, and `actionContext`: planning scope and edit constraints
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns:
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using `/opsx:continue`
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

4. **Read context files**

   Read every file path listed under `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Implement tasks (loop until done or blocked)**

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

7. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: suggest archive
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

All tasks complete! You can archive this change with `/opsx:archive`.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly

<!-- keel:openspec-surface-overlay version=5.7.0 -->
## Keel Apply Overlay

Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.

### Target-native subagent gate

- The current agent remains responsible for Keel ownership, task/archive decisions, scope control, and final reporting.
- Use a target-native subagent only when the current agent decides it is useful for a bounded helper step.
- Target-native subagents return report/evidence only; the current agent reviews the output before acting.
- The subagent brief must name the selected change/task, required read context, allowed write boundary or read-only diagnostic scope, expected commands/evidence, and prohibited actions.
- Prohibited actions include scope expansion, Acceptance changes, completion marking, sync/archive decisions, commits, handoff changes, and cross-runtime delegation unless the selected task or user explicitly authorizes them.
- The current agent remains the Keel task owner and selects one unchecked task or a small contiguous task group from `tasks.md`.
- Run the Task Authoring Gate: each relevant critical expectation must be covered by a slice, deferred to a durable owner, or explicitly discarded.
- Run the Slice Start Gate: selected current slices must name source expectations and include Read, Touch, Acceptance, Commands, and Stop/Autonomy boundaries before implementation.
- Rough future slices may remain drafts, but cannot be selected for implementation or marked complete.
- Obey the selected task contract: Read is required starting context, Touch is the write boundary, Commands prove Acceptance, and the Autonomy boundary controls fallback decisions.
- Target-native subagents return report/evidence only; they cannot mark tasks complete, update OpenSpec state, commit, sync, archive, or change Acceptance.
- The current agent reviews all subagent output, command evidence, and diffs before marking any task complete.
- When implementation exposes a material expectation, acceptance boundary, or user-owned decision absent from durable authority, stop before implementing that choice, rerun `keel-align-expectations`, and reauthor the affected proposal/design/spec/task authority first.
- A discovered repository fact that does not change accepted behavior or scope may be recorded and execution continues inside the existing task boundary without a product interview.
- Invoke OpenSpec through `keel openspec` (for example `keel openspec validate`); a bare `openspec` command may not be on PATH.
- Consult the repository's standing authorization in `keel/config.yaml` before asking the user to confirm a repository action: a standing-authorized action proceeds without a per-occurrence confirmation, and an undeclared action still requires the confirmation it requires today.
- A standing authorization covers the action and never substitutes for a gate, evidence, or Review; it removes the confirmation, not the record, and it is not a trigger to perform the action.
<!-- keel:openspec-surface-overlay:end -->
