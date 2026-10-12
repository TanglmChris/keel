# Tasks

## 1. Quota thresholds

- [x] 1.1 `--quota` reports each threshold once per period, and `--nudge` pauses near the limit
  - Covers:
    - keel-coordinator-patrol / Quota thresholds are reported once each, and nudging pauses near the limit / Each threshold is reported once, and a new period starts over
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
  - Read:
    - src/core/patrol.js
  - Touch:
    - src/core/patrol.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-quota` runs `keel patrol --since-last --notify --nudge --idle 1s` as `rtl` with `verify` holding an addressed message and `KEEL_PATROL_UNREAD_EVERY_MS=1`, at `--quota` 50, 91, 93, 96, 10, 92, and requires the `risk:` quota lines to be none, `past 90%`, none, `past 95%`, none, `past 90%`; `verify` nudged at 50 and not at 91 with `nudges paused: quota at 91%` printed; each reported threshold sent to `rtl` from `keel-patrol`; and `--quota 120` refused. Fails with: `patrol-quota:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9585675b469a3f05ef498b9be6515cf32e4f3837519dc13daa82501c8c5c1233
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-quota` reports `patrol-quota scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-quota: verify was not nudged at 50%: ''`, carrying the declared signature `patrol-quota:` — `--quota` was an unknown argument.
    - M1.green: pass. With `quotaRisk` and the pause: at 50, 91, 93, 96, 10, 92 the quota `risk:` lines are none, `past 90%`, none, `past 95%`, none, `past 90%`; `verify` is nudged at 50 and not at 91, where `nudges paused: quota at 91%` prints; three quota messages reach `rtl` from `keel-patrol`; `--quota 120` exits 1.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 273 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel patrol` six times with the host's figure and an addressed message waiting, and reads stdout, the exit code, and the chat log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7b83b22078d26f32fecb420d8cd42c74e61387cd2abd66fb9ca7fbb62848891c
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.123.0; with the 5.123.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
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

- E1: The coordinator hears about the quota only at the owner's thresholds, once each per period, and nudges stop near the limit (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.123.0 tree reports `validation --all passed: baseline plus 273 scenarios, 1 skipped: output-survives-the-pipe.`
