# Tasks

## 1. Risk-only escalation

- [x] 1.1 `--notify` sends only risks, and every run is logged
  - Covers:
    - keel-coordinator-patrol / A patrol run reports only what changed since the last one / Only a change is reported, once
    - keel-coordinator-patrol / A patrol run reports only what changed since the last one / Only risks reach the coordinator, and every run is logged
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
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-since-last` requires the second run to report the shift and remote changes, exit 2, and send no `keel-patrol` message; and `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-escalate` requires, with `KEEL_PATROL_UNREAD_EVERY_MS=1` and `--idle 1s`, one `keel-patrol` message to `rtl` naming the dirty checkout after a file is added to it, one naming free disk after `--disk-free-gb 12` and none on a repeat at 12, one naming `verify` and `2 nudges` after two unanswered unread nudges, `risk:` lines in the output, and `patrol/log/rtl.log` holding one line per run with `exit=` and `risks=`. Fails with: `patrol-escalate:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a0c6f84f463ea2faf879aad119df792efb4686e49d03ea99aa1e6de90b7d82cf
    - M1: pass. `patrol-since-last` reports `patrol-since-last scenario passed.` and `patrol-escalate` reports `patrol-escalate scenario passed.`
    - M1.red: fail. With the scenarios written first, `patrol-escalate` reported `patrol-escalate: the risk is not printed: 'changed: checkout …: 0 uncommitted paths -> 1 uncommitted paths…'`, carrying the declared signature `patrol-escalate:`; `patrol-since-last` reported that a run with no risk sent the coordinator a notice listing shift, remote, and drift changes.
    - M1.green: pass. With the risk computation, `notifyRisks`, the unanswered count, and `appendRunLog`: the shift and remote changes print and send nothing; the dirty checkout, `--disk-free-gb 12`, and `verify`'s two unanswered nudges each reach `rtl` once from `keel-patrol`, a repeat at 12 GB sends nothing, `risk:` lines print, and `patrol/log/rtl.log` holds one line per run with `exit=` and `risks=`. `patrol-nudge` still passes.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 272 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenarios run the real `keel patrol` against a repository with a bare remote, an untracked file in the primary checkout, and real nudges, and read the chat log, stdout, and the run log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/307 — part 2 (quota thresholds) adds its own risk and the nudge pause at 90 % in the next change.
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
    - Contract: keel-task-capsule/v1 sha256:5a6626eca0926915cc3b63f0eb23223f026418606ae8c28ddc15f2e07c236c57
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.122.0; with the 5.122.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
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

- I1: "Add `--notify` and the changes go to the coordinator as one direct message from `keel-patrol`" — `README.md` Coordinator patrol, and "`--notify` sends those changes to the patrolling role" in the 5.115.0 changelog entry, which stays as history. Updated by: 1.1

## Expectation Coverage

- E1: The coordinator is woken only for risks, while every run stays auditable (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.122.0 tree reports `validation --all passed: baseline plus 272 scenarios, 1 skipped: output-survives-the-pipe.`
