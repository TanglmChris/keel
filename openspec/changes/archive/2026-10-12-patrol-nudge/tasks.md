# Tasks

## 1. Nudges

- [x] 1.1 `keel patrol --nudge` nudges idle roles for unread, shift, and resume, rate-limited, and `ready --wake` marks the note
  - Covers:
    - keel-coordinator-patrol / The patrol nudges idle roles directly / Roles are nudged once each, and parked notes are left alone
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - F1
    - F2
    - F3
    - F4
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` binds `rtl` (the coordinator), `verify`, and `lint`, has `rtl` mention `verify`, and with `--idle 1s` requires: `keel patrol --nudge --context lint=40` nudging `verify` for unread and not `lint`, exiting 2, with a `keel-patrol` record waking `verify`; `--context lint=62` then nudging `lint` for its shift naming `keel shift ready --wake` and `Remote Control`, and not `verify` again; a further run nudging nobody and exiting 0; after `lint` runs `keel shift ready --wake` with a waiter that gives up and `verify` runs `keel shift ready`, a run nudging `lint` to resume and not `verify`; and no run printing `nudged lint: unread`. Fails with: `patrol-nudge:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:989f3a85a048982c0f113c32c9e5543ea56600cf1278a301448b66b72a6e3862
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` reports `patrol-nudge scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-nudge: verify was not nudged for unread: '' 'keel patrol: Unknown argument --nudge. …'`, carrying the declared signature `patrol-nudge:`.
    - M1.green: pass. With `nudgeRoles`, the note's self-initiated line, and `check` ignoring Keel's own senders: the first run nudges `verify` for unread and not `lint` at 40 %, exits 2, and `notice --check` for `verify` sees the `keel-patrol` record; at 62 % the second run nudges only `lint`'s shift, naming `keel shift ready --wake` and `Remote Control`; the third nudges nobody and exits 0; after `lint`'s `ready --wake` with a waiter that gives up at once and `verify`'s parked `ready`, the fourth nudges `lint` to resume and not `verify`; `nudged lint: unread` never appears. The first green attempt found that `lint`, nudged to change its shift, was refused by `keel shift check` over that very nudge; D6 was added and the contract re-recorded, after which `verify`'s `ready` in the scenario takes `--force-reason`, as a parked role with unread work must.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 271 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel patrol --nudge`, `keel shift ready`, and `keel chat notice --check` across three bound worktrees with a bare remote, reading the output lines, exit codes, and the chat log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `src/core/shift.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/307 — parts 2 (quota thresholds) and 3 (risk-only escalation and the run log) follow in their own changes.
    - Blocker: none
    - Reauthorizations: 1. D6 (`keel shift check` ignores unread from `keel-patrol` and `keel-shift`) was added after the first green attempt exposed the refusal; the contract was re-recorded with `task-start --record` before any Evidence was written.
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:01ff9b5442bf59e32415f5cde65129eca21c6c0be55986c2462d68f191730a01
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.121.0; with the 5.121.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
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

- None.

## Expectation Coverage

- E1: An idle role is nudged directly, rate-limited, over what is addressed to it, its context, or its own unresumed shift, while a parked role and Keel's own messages never trigger a nudge (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.121.0 tree reports `validation --all passed: baseline plus 271 scenarios, 1 skipped: output-survives-the-pipe.`
