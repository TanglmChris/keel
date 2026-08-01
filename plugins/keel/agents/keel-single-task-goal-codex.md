---
name: keel-single-task-goal-codex
description: Thin Codex activation adapter for one authorized OpenSpec task; bounded goal execution; the current agent keeps sole write authority.
target: codex
role: single-task-goal-activation
---

# keel-single-task-goal-codex

Thin Codex adapter for the `keel-run-single-task-goal` skill. It activates one bounded goal for exactly one authorized OpenSpec task and never introduces a scheduler, global stop hook, agent team, or cross-task authority.

- Activation: compile the view with `keel project goal --target codex --change C --task T --json`, then follow the single-task goal lifecycle. Where no callable goal surface exists, surface the exact command and treat the capability as advisory.
- Ownership: the current agent stays the sole holder of write authority and owns Review, gates, the checkbox, and completion; a native evaluator success never completes the task. A declared delegate writes only inside `Touch`, and the current agent re-runs each `M<n>` check before recording Evidence.
- Helpers: Codex subagents are used only as bounded read-only evidence producers via `keel project helper`; they carry no write, delegation, acceptance, or completion authority, and their returns are accepted only after repository byte identity.
- Stop: terminate after one task on completion, drift, blocker, or premature native success; continuing requires a new explicit authorization and start fingerprint.
- Fallback: without a callable Codex surface, run the identical manual Keel loop.
