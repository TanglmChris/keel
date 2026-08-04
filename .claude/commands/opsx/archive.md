---
name: "OPSX: Archive"
description: Archive a completed change in the experimental workflow
allowed-tools: Bash(openspec:*)
category: Workflow
tags: [workflow, archive, experimental]
---

Archive a completed change in the experimental workflow.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name after `/opsx:archive` (e.g., `/opsx:archive add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - `artifacts`: List of artifacts with their status (`done` or other)

   **If any artifacts are not `done`:**
   - Display warning listing incomplete artifacts
   - Prompt user for confirmation to continue
   - Proceed if user confirms

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete).

   **If incomplete tasks found:**
   - Display warning showing count of incomplete tasks
   - Prompt user for confirmation to continue
   - Proceed if user confirms

   **If no tasks file exists:** Proceed without task-related warning.

4. **Assess delta spec sync state**

   Use `artifactPaths.specs.existingOutputPaths` from status JSON to check for delta specs. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   If user chooses sync, use Task tool (subagent_type: "general-purpose", prompt: "Use Skill tool to invoke openspec-sync-specs for change '<name>'. Delta spec analysis: <include the analyzed delta spec summary>"). Proceed to archive regardless of choice.

5. **Perform the archive**

   Create an `archive` directory under `planningHome.changesDir` if it doesn't exist:
   ```bash
   mkdir -p "<planningHome.changesDir>/archive"
   ```

   Generate target name using current date: `YYYY-MM-DD-<change-name>`

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move `changeRoot` to the archive directory

   ```bash
   mv "<changeRoot>" "<planningHome.changesDir>/archive/YYYY-MM-DD-<name>"
   ```

6. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Spec sync status (synced / sync skipped / no delta specs)
   - Note about any warnings (incomplete artifacts/tasks)

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** ✓ Synced to main specs

All artifacts complete. All tasks complete.
```

**Output On Success (No Delta Specs)**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** No delta specs

All artifacts complete. All tasks complete.
```

**Output On Success With Warnings**

```
## Archive Complete (with warnings)

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** Sync skipped (user chose to skip)

**Warnings:**
- Archived with 2 incomplete artifacts
- Archived with 3 incomplete tasks
- Delta spec sync was skipped (user chose to skip)

Review the archive if this was not intentional.
```

**Output On Error (Archive Exists)**

```
## Archive Failed

**Change:** <change-name>
**Target:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/

Target archive directory already exists.

**Options:**
1. Rename the existing archive
2. Delete the existing archive if it's a duplicate
3. Wait until a different date to archive
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, use the Skill tool to invoke `openspec-sync-specs` (agent-driven)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting

<!-- keel:openspec-surface-overlay version=5.27.0 -->
## Keel Archive Overlay

Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.

### Target-native subagent gate

- The current agent remains responsible for Keel ownership, task/archive decisions, scope control, and final reporting.
- Use a target-native subagent when the current agent decides it is useful for a bounded helper step, or as a delegate implementing the selected task where `delegation:` is declared in `keel/config.yaml` and a guard manifest is active.
- Target-native subagents acting as helpers return report/evidence only. A delegate may write, and only inside `Touch`; its reported command results are a claim, and the current agent re-runs each `M<n>` check itself before recording Evidence.
- Delegation is refused with no active guard manifest, because an absent manifest passes every write through silently and looks identical to a checked one.
- Neither may mark tasks complete, update OpenSpec state, commit, sync, archive, or change Acceptance; the current agent reviews all output before acting.
- The subagent brief must name the selected change/task, required read context, allowed write boundary or read-only diagnostic scope, expected commands/evidence, and prohibited actions. Compile it with `keel project --event subagent-start --authorize subagent`; Keel adds no separate carrier because the host already has one.
- Prohibited actions include scope expansion, Acceptance changes, completion marking, sync/archive decisions, commits, handoff changes, and cross-runtime delegation unless the selected task or user explicitly authorizes them.
- The current agent owns final sync/archive decisions and must verify task evidence, follow-up ownership, and completion gates before proceeding.
- Before final sync/archive, each related critical expectation must have behavior evidence, a durable follow-up owner, or an explicit discard reason.
- Target-native subagents may help with bounded assessment or evidence production only; they cannot archive, sync, change acceptance, or bypass completion gates.
- The current agent reviews any subagent report before running `openspec-sync-specs`, `/opsx:sync`, or `/opsx:archive`.
- Do not treat generic OpenSpec archive delegation language as authority to transfer Keel ownership.
- Invoke OpenSpec through `keel openspec` (for example `keel openspec validate`); a bare `openspec` command may not be on PATH.
- When `/opsx:sync` has already promoted the change's spec delta, run the archive with `--skip-specs` so the promoted delta is not re-applied; archive is not idempotent over an already-synced delta.
- After archiving, run `keel guard clear` to drop the change's guard manifest; the read-only gate never clears it for you.
- A repository that standing-authorizes `archive` in `keel/config.yaml` does not need the per-occurrence archive confirmation; a repository that declares nothing still needs it.
- The completion gate and follow-up ownership checks still run unchanged under a standing authorization; it removes the confirmation, not the proof.
<!-- keel:openspec-surface-overlay:end -->
