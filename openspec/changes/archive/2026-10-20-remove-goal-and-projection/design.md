## Context

A read-only inventory on 2026-10-20 mapped every dependency of the three removed features.

## Facts

- F1 — Module dependencies:
  - Only `bin/keel.js` requires `goal.js`, `helper.js`, and `tasksview.js`.
  - `projection.js` is also required by `src/core/agents.js:486`. `keel agents brief` calls `projectRuntime` with `projectionEvent: "subagent-start"` and reads `objective`, `acceptance`, `read`, `touch`, `evidenceContract`, `prohibitions`, and `fingerprint`. For implementation it relies on `delegationRefusal`: an active guard whose change, task, fingerprint value, and sorted Touch match.
- F2 — `task-contract.js` hashes the whole capsule. The capsule always carries `helperAuthority: "read-only-evidence-only"`, and carries `delegation` only when a tier resolves.
  - Removing `helperAuthority` would move every recorded fingerprint in every repository. The owner chose to keep it.
  - No repository on this machine declares `delegation:` or a task `Delegation:` field (checked in keel, kaiwu-ip, and chip_sec_flow_v2 live changes). Removing it moves no live fingerprint.
- F3 — `keel-surface-evolution-policy` forbids retiring a projection surface without a durable first-party coverage report. D1 is that report.
- F4 — The startup, resume, compaction, and worktree events have their own consumers (`capabilities.js`, the `stateless-continuity` and `native-runtime-projection` scenarios, `README.zh-CN.md`) and stay.

## Decisions

- D1 — Coverage report (first-party host capabilities that replace each retired surface, as of Claude Code 2.1.304 and codex-cli 0.163.0):

  | Retired surface | Covered by |
  |---|---|
  | `/goal` skill, agents, `keel project goal` | native `/goal` on Claude and Codex |
  | `keel project helper` | native subagents on both hosts |
  | subagent projection | native subagents |
  | `keel project tasks` / task-view | the native todo / task list |

  In each case the gates, fingerprints, and the `Touch` write guard still bind whoever runs the step. The guard reads no subagent field (#414 audit), so it treats a native goal or subagent exactly as it treats the main agent.
- D2 — `keel agents brief` keeps its behavior.
  - A private `compileTaskBrief` in `agents.js` replaces the `projectRuntime(subagent-start)` call. It resolves context, compiles the capsule, refuses a task that is not ready, missing, or complete, refuses an implementation brief without an active manifest matching change, task, fingerprint, and Touch, and returns the fields the brief renders.
  - The prohibitions the subagent event added stay in the brief text.
- D3 — The capsule keeps `helperAuthority` as a constant, with a comment that it is kept only for fingerprint stability and nothing reads it. `delegation` leaves the capsule. A task `Delegation:` line is no longer a known field.
- D4 — `--authorize`, `--subagent-mode`, `--native-complete`, and `--expected-fingerprint` are removed with their events. `keel project` then accepts only `--event startup|resume|compaction|worktree`.
- D5 — A new scenario, `native-projections-removed`, holds the removal:
  - `keel project goal`, `keel project tasks`, `keel project helper`, and `--event subagent-start` each exit nonzero;
  - doctor prints no `execution.goal` or `helper` line;
  - neither the skill nor `plugins/keel/agents/` ships, and no manifest names an agent.
