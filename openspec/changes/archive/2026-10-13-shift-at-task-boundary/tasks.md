# Tasks

## 1. Task-boundary shift

- [x] 1.1 The shift nudge follows a closed todo, and `--context`/`--shift-at` are retired
  - Covers:
    - keel-coordinator-patrol / The patrol nudges idle roles directly / Roles are nudged once each, and parked notes are left alone
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - src/core/patrol.js
  - Touch:
    - src/core/patrol.js
    - docs/shift-change.md
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` follows the scenario with `--idle 1s`: `rtl` assigns `lint` two todos that `lint` reads and mentions `verify`; run 1 nudges `verify` for unread and not `lint`; after `lint` closes one todo, run 2 prints `nudged lint: shift` with a message naming `keel shift ready --wake`; run 3 nudges nobody and exits 0; after `lint` closes the other, run 4 nudges `lint` with a message naming `wait for the coordinator` and not `--wake`; after `lint`'s `ready --wake` and `verify`'s parked `ready`, run 5 nudges `lint` to resume and not `verify`; `nudged lint: unread` never appears; and `--context lint=62` exits 1 naming `retired`. Fails with: `patrol-nudge:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6805f979129df1be828d04a3fb04740e15da494eb9a116091b3d3327518b98b4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` reports `patrol-nudge scenario passed.`
    - M1.red: fail. With the scenario rewritten first, it reported `patrol-nudge: closing a todo should nudge only lint's shift: 'keel patrol: nothing new. …'`, carrying the declared signature `patrol-nudge:`.
    - M1.green: pass. With `closedTodos`, the `closedSeen` baseline, the task-boundary message, and the retired flags: run 1 nudges `verify` for unread and not `lint`; after `lint` closes R009, run 2 prints only `nudged lint: shift`, naming `keel shift ready --wake` and Remote Control; run 3 nudges nobody and exits 0; after R010 closes, run 4 nudges `lint` naming `wait for the coordinator` and not `--wake`; run 5 nudges `lint` to resume and not the parked `verify`; `nudged lint: unread` never appears; `--context lint=62` exits 1 naming `retired`. A first green attempt skipped every nudge on a role's first look because the baseline step ended the loop; it now only records existing closures.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario assigns and closes real todos with `keel chat todo` and `keel chat done`, runs the real `keel patrol --nudge` five times, and reads stdout, exit codes, and the chat log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `docs/shift-change.md`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a role whose work is not assigned through `keel chat todo` gets no task-boundary nudge; the owner chose closed todos as the signal over closed issues.
    - Blocker: none
    - Reauthorizations: none
## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-coordinator-patrol/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d3acc6fd176a3bca207f8478323962a07022b97a09b8c5f8af0ca0ae18954b56
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.125.0; with the 5.125.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its counterpart in `openspec/specs/keel-coordinator-patrol/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the promoted spec are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "when the host reports with `--context <role>=<percent>` that its context is at or above `--shift-at`" — `README.md` Coordinator patrol, and the 5.121.0 notice sent to rtl_ppa_prj's coordinator. Updated by: 1.1

## Expectation Coverage

- E1: A role is told to change shift when it finishes a task — with or without its next one in hand — and never mid-task because of context size (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.125.0 tree reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`
