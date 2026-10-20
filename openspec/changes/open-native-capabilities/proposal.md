## Why

Issue #414 (owner, 2026-10-20): bare Claude Code reaches for subagents and the todo list far more often than a Keel session does. Measured from `~/.claude/projects/*/*.jsonl` that day, subagent calls per 1000 tool calls were 0.00 in keel, 0.12 in kaiwu-ip, and 0.85 elsewhere. Two read-only audits found Keel mechanically blocks only Edit/Write outside `Touch` (while a guard manifest exists) and `git push` (while push grants are declared). Every other suppression is model-facing text: prohibitions, ceremony, and wording that tells the model to stay in one session, take one task, read only a minimal list, or stop after two attempts.

The owner reviewed each item and set the stance: Keel neither suppresses nor steers native capabilities — "不抑制，也不给倾向". The model decides whether to use a subagent, a todo list, another file, or another attempt. The gates, the `Touch` write guard, routing, verification discipline, and the safety and outward boundaries stay.

## What Changes

- **Subagents** are the model's choice and are treated as the main agent is: the same gates, `Touch` guard, and evidence rules apply to whoever runs a step. Removed from the protocol, the consumer bootstrap, and the generated apply/archive/sync surfaces: the ownership clauses, the helper/delegate split, the mandatory brief, the refusal without a guard manifest, the rerun duty, the prohibited-action list, and "bounded assessment only". External model CLIs keep their allowlist, egress, and worktree refusals.
- **Todo list**: the sentence "goal/task-view projection requires explicit authorization", which reads as a rule about the native task list, is removed. Nothing is added in its place.
- **Continuing**: by default the agent works through the unchecked tasks of an approved `tasks.md` in order. Each task still starts through `keel gate task-start` and completes through `keel gate task-complete`, and every stop trigger still stops. `continuation` stays in the authorization vocabulary and is redundant.
- **Memory, transcripts, Git state** may inform the agent; `keel context` decides the current task.
- **Retrying**: `keel-debug-failure` drops its two-attempt cap. A stop still reports the original error and what changed in each attempt.
- **Reading**: "Read only the documents needed", "minimal read list", "load only that one", "do not load unrelated lenses", and "read only the returned paths" are removed.
- The `/goal` customization (`keel-run-single-task-goal`, its agents, `keel project goal`/`helper`) is removed in a separate change.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-openspec-surface-overlay`: the apply, archive, and sync surfaces no longer assign ownership or restrict subagents, and apply continues through an approved task list.
- `keel-standing-authorization`: continuing to the next task needs no authorization; `continuation` is accepted and redundant.

## Impact

`AGENTS.md`, `assets/bootstrap/AGENTS.md`, `bin/keel.js` (overlay text), the regenerated `.claude/` and `.codex/` OpenSpec surfaces, `assets/openspec/schemas/keel-spec-driven/schema.yaml`, five skills and their plugin copies, `README.md`, `README.zh-CN.md`, `scripts/validate_plugin.py`, the published specs, and the changelog.
