# Tasks

## 1. Patrol on a host task

- [x] 1.1 `keel patrol --since-last` reports only changes, and `--notify` sends them to the coordinator
  - Covers:
    - keel-coordinator-patrol / A patrol run reports only what changed since the last one / Only a change is reported, once
    - D1
    - D2
    - F3
    - F5
  - Read:
    - src/core/patrol.js
    - src/core/shift.js
  - Touch:
    - src/core/patrol.js
    - src/core/shift.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-since-last` uses roles `rtl` (the coordinator) and `verify` with a bare remote, and requires: `keel patrol --since-last --notify` by `rtl` printing `baseline recorded` and exiting 0; after `verify` runs `keel shift ready` and a new commit is pushed and fetched, a second run exiting 2 with `changed:` lines naming the shift status and the remote, and exactly one record from `keel-patrol` for `rtl` with `keel chat notice --check` for `rtl` exiting 0; a third run exiting 0 with no `changed:` line and still one `keel-patrol` record; and `--notify` without `--since-last` exiting 1. Fails with: `patrol-since-last:`
    - M2 (regression): `coordinator-patrol`, `patrol-issue-routing`, and `patrol-rearm` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ae077c86bc95670f88d4fe4fc1450b9c30c45798efd1ab547c51e73b52b3fa0e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-since-last` reports `patrol-since-last scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-since-last: the first run did not record a baseline quietly (exit 1): … Unknown argument --since-last`, carrying the declared signature `patrol-since-last:`.
    - M1.green: pass. With the per-role snapshot, `changed:` lines, and the `keel-patrol` notice: `--notify` alone exits 1, the first run prints `baseline recorded` and exits 0 with no notice, the run after `verify`'s `ready` and a pushed commit exits 2 naming `shift verify` and `remote origin/main` with exactly one `keel-patrol` record that `notice --check` for `rtl` sees, and the third run exits 0 with no `changed:` line and no second notice.
    - M2: pass. `coordinator-patrol`, `patrol-issue-routing`, and `patrol-rearm` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel patrol`, `keel shift ready`, git push to a bare remote, and `keel chat notice --check`, reading exit codes, stdout, and the chat log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `src/core/shift.js` (exports only), `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
- [x] 1.2 `patrol:` declares the host task and model, the reminder follows it, and `keel patrol task` renders the task
  - Covers:
    - keel-coordinator-patrol / The patrol's host task is declared and rendered, never installed by Keel / The host task is rendered from the declaration
    - keel-coordinator-patrol / The patrol's host task is declared and rendered, never installed by Keel / A declared host task changes the reminder
    - D3
    - D4
    - F1
    - F2
    - F4
    - F6
  - Read:
    - src/core/config.js
    - src/core/patrol.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/config.js
    - src/core/patrol.js
    - src/core/context.js
    - src/core/shift.js
    - plugins/keel/scripts/session-start.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-host-task` declares `patrol:` with `role: rtl`, `every: 30m`, `host_task: soc-patrol`, and requires: `keel patrol task` printing `soc-patrol`, `*/30 * * * *`, a statement that no model is declared, and `keel patrol --repo <rtl worktree> --since-last --notify`, with `git status --porcelain` unchanged; with `model: small-model` added, the output naming `small-model`; `keel context --json` in `rtl` carrying `patrol.hostTask` `soc-patrol` and the session-start note naming `soc-patrol` and `still enabled`; `host_task: Bad_Id` reported by name; and `keel patrol task` refused when no worktree is bound to the role. Fails with: `patrol-host-task:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9ab257ef517dee33d65c68d6ca61024a2eafe2dd23d3c3d8c1f7c4c7dd41d78e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-host-task` reports `patrol-host-task scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-host-task: keel patrol task failed:  keel patrol: Unknown argument task.`, carrying the declared signature `patrol-host-task:`.
    - M1.green: pass. With `host_task:`/`model:` read by `readPatrolDeclaration`, the host-task reminder in config, context, `shift resume`, and session-start, and `keel patrol task`: it is refused with no worktree bound to `rtl`; once bound it prints `soc-patrol`, `*/30 * * * *`, `no model is declared`, and `keel patrol --repo <rtl> --since-last --notify` with `git status --porcelain` unchanged; with `model: small-model` it prints that model; `keel context --json` carries `patrol.hostTask` `soc-patrol`; the session-start note names `soc-patrol` and `still enabled` and not "re-create it with the host"; and `host_task: Bad_Id` is reported by name. A render against a scratch repository declaring `every: 60m` printed `0 * * * *`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 265 scenarios, 1 skipped: output-survives-the-pipe.` A first run failed `assertion-shape-count` (82 or-guarded sites against 80) on three combined assertions in the two new scenarios; each was split into its own message, `assertion-shape-count` reports 80, and `patrol-since-last` still passes.
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real `keel patrol task`, `keel context --json`, and the plugin's SessionStart hook, reading stdout, warnings, and the worktree status.
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/patrol.js`, `src/core/context.js`, `src/core/shift.js`, `plugins/keel/scripts/session-start.js`, `keel/config.yaml`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: whether a desktop scheduled task's session starts inside the worktree it names is not observable from Keel; the rendered prompt runs every command by path and forbids changing into it, so the run does not act as the role either way.
    - Blocker: none
    - Reauthorizations: 1. D4's wording for an undeclared model was corrected in design.md from `not declared: …` to `no model is declared: …`, the text M1 asserts and the implementation prints; it moved the fingerprint, and `task-start --record --keep-evidence M1 --keep-evidence M2` re-anchored it. Neither check's assertion moved, and both were re-run on the final tree (`patrol-host-task scenario passed.`; `npm test` 265 scenarios).
## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-coordinator-patrol/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirements are appended to `openspec/specs/keel-coordinator-patrol/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:64febc058202b7188aa9c86bf17e920f23c592c03b96a592d28af3635961c021
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.115.0; with the 5.115.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements are appended to `openspec/specs/keel-coordinator-patrol/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the promoted spec are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 and 1.2 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "re-create it with the host if this session has none" — the patrol reminder in `src/core/config.js`, the session-start line in `plugins/keel/scripts/session-start.js`, and "are reminded to re-create it" in `README.md` and `keel/config.yaml`: untrue once a host task is declared. Updated by: 1.2
- I2: "writes nothing when nothing is new" — `README.md` Coordinator patrol: `--since-last` writes its snapshot on every run. Updated by: 1.1

## Expectation Coverage

- E1: An hourly patrol wakes the coordinator only when something changed, with no model judgment in the scheduled run (D1, D2). Covered by: 1.1
- E2: The patrol runs as a host task that outlives the coordinator's session, which Keel renders and declares but never installs or picks a model for (D3, D4). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.115.0 tree reports `validation --all passed: baseline plus 265 scenarios, 1 skipped: output-survives-the-pipe.`
