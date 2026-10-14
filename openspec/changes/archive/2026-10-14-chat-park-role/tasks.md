# Tasks

## 1. Park a role

- [x] 1.1 `keel chat role --park/--unpark`; posts say parked; patrol leaves a parked role alone
  - Covers:
    - keel-cross-host-mailbox / A role can be parked on purpose / A todo for a parked role says it is parked
    - keel-coordinator-patrol / The patrol nudges idle roles directly / A parked role is left alone
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/chat/drift.js
    - src/core/patrol.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/chat/drift.js
    - src/core/patrol.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-park-role` runs the real commands: `keel chat role --park ghost` exits non-zero; with `@verify` waiting past `--idle`, `rtl` runs `keel chat role --park verify --reason "until R040"`, then `keel chat todo soc --assignee verify` names `verify` as parked with `until R040` (and `parked` in `--json`); two `keel patrol --nudge --idle 1s` runs nudge nobody, report no risk for `verify`, print no drift for it, and print `verify`'s role line with `parked`; `keel chat role --unpark verify` reports the waiting records; the next patrol nudges `verify`; a park followed by a `verify` session-start hook is no longer in effect. Fails with: `does not say verify is parked`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` and `--scenario chat-wake-idle-desktop` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6f7da75c0a105a9e1a884321f4a246c84d9fad9ad2d14a98263099ba5c00c316
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-park-role` reports `chat-park-role scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `chat-park-role: a todo for a parked role does not say verify is parked: Posted 20261014T155313234Z-rtl-a1ff77 to soc. (--park: keel chat: Unknown option for keel chat: --park)`, carrying the declared signature `does not say verify is parked`.
    - M1.green: pass. With `notice.park/parkOf/unpark`, `keel chat role --park/--unpark`, the parked line in `postResult`, and `nudgeRoles`/`roleDrift` skipping a parked role, the scenario passed.
    - M2: pass. `--scenario patrol-nudge` reports `patrol-nudge scenario passed.`; `--scenario chat-wake-idle-desktop` reports `chat-wake-idle-desktop scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 283 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0). The first run failed `assertion-shape-count` (82 vs 80) on two `or`-joined checks in the new scenario; both were split so each failure carries its own message.
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real `chat role --park/--unpark`, `chat todo` (text and `--json`), `patrol --nudge` twice while parked and once after, and the real session-start hook ending a park; each assertion reads command output.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/chat/drift.js`, `src/core/patrol.js`, `scripts/validate_plugin.py`, both chat docs, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the specs
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
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement joins `keel-cross-host-mailbox` and the MODIFIED one replaces its counterpart in `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e5b775cd20424c0525004a71e7c8d69d266784f66a9e47a25dde4e05bb338201
    - M1: `node scripts/bump_version.js minor` moved every marker 5.137.0 → 5.138.0; with the "A role can be parked on purpose" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the ADDED requirement joined `keel-cross-host-mailbox` and the MODIFIED one replaced its counterpart in `keel-coordinator-patrol`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and both published specs carry the change; both validator scenarios pass.
      - Scope check: changed files are the version markers, `keel/CHANGELOG.md` and the two published specs, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "MUST send an idle role one direct message from `keel-patrol`" with no exception for a parked role — `openspec/specs/keel-coordinator-patrol/spec.md`. Updated by: 2.1
- I2: "keel chat role [--set <name>] [--alias <alias>] [--prune] [--json]", the usage line that names no park — `src/core/chat/cli.js`. Updated by: 1.1

## Expectation Coverage

- E1: A role parked on purpose is not nudged or reported as a risk, and posters are told it is parked (#316, D4, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
