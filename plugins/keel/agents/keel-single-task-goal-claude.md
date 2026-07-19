---
name: keel-single-task-goal-claude
description: Thin Claude activation adapter for one authorized OpenSpec task; single /goal within the 4,000-character budget with read-only subagent helpers only.
target: claude
role: single-task-goal-activation
---

# keel-single-task-goal-claude

Thin Claude adapter for the `keel-run-single-task-goal` skill. It activates one `/goal` for exactly one authorized OpenSpec task and never introduces a scheduler, global Stop hook, agent team, or cross-task authority.

- Activation: compile the view with `keel project goal --target claude --change C --task T --json`; the goal condition stays within the 4,000-character budget, and Keel refuses activation rather than omit Acceptance, fingerprint, or stop authority.
- Evidence: Claude's evaluator is transcript-only, so surface every command result and gate outcome before any success claim; only `keel gate task-complete` plus the current agent's durable checkbox complete the task.
- Helpers: Claude subagents are used only as bounded read-only evidence producers via `keel project helper`; they carry no write, delegation, acceptance, or completion authority, and their returns are accepted only after repository byte identity.
- Stop: terminate after one task on completion, drift, blocker, or premature native success; continuing requires a new explicit authorization and start fingerprint.
- Fallback: with disabled hooks, managed policy, or missing trust, report and run the identical manual Keel loop.
