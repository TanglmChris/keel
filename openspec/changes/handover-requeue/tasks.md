# Tasks

## 1. Claim before starting, settle a dead runner, retry a failed hand-off

- [ ] 1.1 Claim the entry before any host call, adopt a session already started, and retry a failed hand-off three times
  - Covers:
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / Concurrent runners start one session
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / A runner that died while starting is settled without a second start
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / A failed hand-off is retried within a bound
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / A resumed old session or an older entry is not retried
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
  - Read:
    - openspec/changes/handover-requeue/design.md
    - src/core/shift.js
    - src/core/tick.js
  - Touch:
    - src/core/shift.js
    - docs/host-contract.md
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - scripts/validate_plugin.py
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-handover-claims-once`: two `keel tick` processes and a `keel shift handover-wait` started together on one pending hand-off, against a fake `claude` whose `--bg` lists the new session and then takes a second to return, run `--bg` once and deliver the entry; and a tick killed inside a `--bg` that already listed its session, followed by another `keel tick`, leaves the entry delivered with `adopted: true` and that session's id, with `--bg` run once. Fails with: `shift-cli-handover-claims-once:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-retries-failed-handover`: with `--bg` always failing, five ticks run it three times, the entry stays failed, and `keel shift status` and `keel patrol` name `keel chat wake now verify`; with `--bg` failing twice and then succeeding, the entry is delivered on the third attempt; and a failed entry whose old session shows `status: idle` again, or that records no `attempts`, runs no `--bg` over two more ticks. Fails with: `shift-cli-retries-failed-handover:`
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift`, `--scenario shift-cli-keeps-old-sessions`, `--scenario shift-cli-removes-after-exit`, `--scenario shift-cli-names-host-failure`, `--scenario tick-retries-failed-wake`, `--scenario assertion-shape-count`, every `shift-*`, `tick-*` and `patrol-*` scenario, and the baseline pass, and every scenario `docs/host-contract.md` cites is registered.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:81e19be1560338ea15a3434679a79005110cea615673194f1088a94dfd64f39e (keel 5.183.0)
    - M1:
    - M1.red:
    - M1.green:
    - M2:
    - M2.red:
    - M2.green:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: 2026-10-21 11:34, before any Evidence was recorded. #409 (keel-maint-2) moves the shift scenarios into `scripts/validation/shift.py` with the registry in `scripts/validation/registry.py`, so both join Touch. `scripts/validate_plugin.py` stays in Touch for the case where the split has not landed.

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-shift-change/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-shift-change`. `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "recording `delivered` … or `failed` with the reason, once per entry" — `openspec/specs/keel-shift-change/spec.md`, the CLI hand-over requirement. Updated by: 2.1.
- I2: "a real concurrent race between the waiter and a tick" and "re-queueing a `failed` hand-off" under "unverified", and the "New session fails to start" row — `docs/host-contract.md`. Updated by: 1.1.
- I3: "A hand-off that failed, or is still pending after 15 minutes, is a patrol risk" and its Chinese twin "失败的交接，或等待超过 15 分钟的交接，会成为巡检风险" do not mention the retry — `docs/cli-team.md`, `docs/cli-team.zh-CN.md`. Updated by: 1.1.

## Expectation Coverage

- E1: A hand-off starts at most one session even under concurrent or dying runners. A failed hand-off is retried at most three times, and after that the recovery is named (#408; D1–D6). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Follow-ups

- The desktop app path and Codex remain unverified in `docs/host-contract.md`. Durable owner: https://github.com/TanglmChris/keel/issues/408
