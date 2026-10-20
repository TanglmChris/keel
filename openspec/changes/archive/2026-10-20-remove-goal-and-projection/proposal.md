## Why

Issue #414, second half. The owner decided on 2026-10-20 that Keel neither suppresses nor steers native capabilities, and 5.172.0 removed the wording that did. What remains is tooling built for the old stance:
- the `/goal` customization: the `keel-run-single-task-goal` skill, its two agents, `keel project goal`, and `keel project helper`;
- the subagent projection: `keel project --event subagent-start|subagent-stop`, `--subagent-mode`, and `delegation:` tiers;
- the native task-view projection: `keel project tasks` and `--authorize task-view|goal`.

The protocol no longer points at any of it. The goal skill still says continuing needs an explicit instruction and helpers are read-only, which contradicts 5.172.0. The owner chose to remove all of it, and to keep the external-model brief (`keel agents brief`).

## What Changes

- **Removed**:
  - `src/core/goal.js`, `src/core/helper.js`, `src/core/tasksview.js`;
  - the `keel-run-single-task-goal` skill and its plugin copy;
  - `plugins/keel/agents/` and the root manifest's `agents` entry;
  - `keel project goal|tasks|helper` and the `goal`, `task-view`, `subagent-start`, and `subagent-stop` events;
  - `--authorize`, `--subagent-mode`, `--native-complete`, and `--expected-fingerprint`;
  - the `delegation:` declaration and the task `Delegation:` field;
  - the `execution.goal`, `execution.task-view`, `delegation.*`, and `helper` doctor lines.
- **Kept**:
  - `keel project` startup, resume, compaction, and worktree views.
  - `keel agents brief`, now compiling its brief from the task capsule directly, with the same refusals, including an active, matching guard for an implementation brief.
  - The capsule's fixed `helperAuthority` field, so that no recorded fingerprint moves (owner decision).
- **Specs**:
  - `keel-single-task-goal-execution` and `keel-authorized-delegation` are retired.
  - The goal, helper, task-view, and subagent requirements are removed from the projection, core-gate, diagnostics, continuity, capsule, guard, and package specs.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-runtime-projection`, `keel-core-gates`, `keel-target-surface-diagnostics`, `keel-task-capsule`, `keel-external-agents`, `keel-touch-write-guard`, `keel-stateless-continuity`, `keel-native-plugin-package`: requirements removed or reworded.
- `keel-single-task-goal-execution`, `keel-authorized-delegation`: retired.

## Impact

- **Source**: `bin/keel.js`, `src/core/{projection,capabilities,config,task-contract,agents}.js`, three deleted modules.
- **Plugin**: the plugin skills, agents, and manifests; the hook script comments.
- **Validation**: `scripts/validate_plugin.py`, with 20 scenarios removed and about 10 edited.
- **Docs**: both READMEs, `AGENTS.md`, the `keel/config.yaml` header, and the two `tasks.md` templates.
- **Specs**: the published specs.
