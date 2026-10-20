## Context

The model reads Keel through:
- the repository's own `AGENTS.md` protocol, maintained in place;
- the consumer bootstrap `assets/bootstrap/AGENTS.md`, installed into other repositories;
- the OpenSpec surface overlays that `bin/keel.js` generates into `.claude/` and `.codex/`;
- the `keel-spec-driven` schema instructions;
- six skills;
- the README.

## Facts

- F1 — Measured 2026-10-20 over `~/.claude/projects/*/*.jsonl`: subagent (`Agent`/`Task`) calls per 1000 tool calls were 0.00 in keel (35 sessions, 5803 calls), 0.12 in kaiwu-ip (220 sessions), and 0.85 elsewhere (18 sessions). Todo-tool calls were 33 in keel and 0 in the other two groups. So the todo data does not show suppression; the wording is removed on the owner's principle, not on measurement.
- F2 — Audits on 2026-10-20 found two mechanical blocks: `plugins/keel/scripts/pretooluse-guard.js` denies Edit/Write/NotebookEdit outside `Touch` while `keel/guard.json` exists, and checks `git push` in Claude Bash while push grants are declared. The guard reads no subagent field, so a subagent is judged exactly as the main agent is. Todo, plan mode, memory, `/goal`, compaction, commits, and subagents have no mechanical block.
- F3 — `continuation` appears in code only as a member of `AUTHORIZATION_ACTIONS` in `src/core/config.js`. No gate or command reads it to decide anything.
- F4 — The owner decided item by item in #414 (comment of 2026-10-20). Decided as kept: the gates and fingerprints, the `Touch` guard, Full/Lite routing and scope, verification discipline, inspecting the repository before asking, plan decisions recorded in OpenSpec, push checks, no unattended merge, external-CLI allowlist and egress, consent for rollback and install, and the read-only Codex waker.

## Decisions

- D1 — Subagents. Every model-facing surface says one neutral thing: a subagent is the model's choice and is treated as the main agent is; the gates, the `Touch` guard, and the evidence rules apply to whoever runs a step.
  - Removed: the ownership clauses, the helper/delegate split, the brief requirement, the refusal without a manifest, the rerun duty, the prohibited-action list, and the archive/sync "bounded assessment only" lines.
  - External model CLIs keep their refusals.
  - The `keel project --event subagent-start` and `keel agents brief` commands are not mentioned as a required step. Their code is unchanged here.
- D2 — Todo. The AGENTS.md clause "goal/task-view projection requires explicit authorization" is removed, and nothing replaces it.
- D3 — Continuing. AGENTS.md, the apply overlay, and the schema say the agent works through an approved `tasks.md` in order, each task through its own `task-start` and `task-complete`, and that every stop trigger still halts.
  - The `keel-standing-authorization` continuation requirement becomes: crossing the boundary needs no authorization, and a declared `continuation` is accepted and changes nothing.
  - Removing the action from the vocabulary would break repositories that declare it.
- D4 — Memory, transcripts, and Git state may inform the agent; `keel context` decides the current task.
- D5 — `keel-debug-failure` keeps the report shape and the coupled-task stop rules, and drops the attempt cap. This answers #410.
- D6 — The reading restrictions are removed from AGENTS.md and the skills. `keel context` still prints its read list. The guidance-tiering instruction ("read `guidance.md` unless `executor_tier: high`") is required by `keel-guidance-tiering` and is out of scope.
- D7 — A new validator scenario, `native-capabilities-unrestricted`, holds every removed phrase out of every model-facing file. It also requires the neutral subagent sentence and the default-continuation sentence in the protocol, the bootstrap, and the apply overlay.
