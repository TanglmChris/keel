# Tasks

## 1. Claim before starting, settle a dead runner, retry a failed hand-off

- [x] 1.1 Claim the entry before any host call, adopt a session already started, and retry a failed hand-off three times
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
    - M1: pass. `shift-cli-handover-claims-once scenario passed.` (`--scenario`, from `scripts/validation/shift.py`, after merging 5.184.0's split).
      - Two `keel tick` processes and a `keel shift handover-wait`, started together against a fake whose `--bg` lists the session and then returns after 1 s, ran `--bg` once, and the entry was delivered.
      - A tick was killed (process group, SIGKILL) inside a 30 s `--bg` that had already listed `verify · …`. Any lock it left was aged ten minutes, and the next tick delivered the entry with `adopted: true` and `new_session: newsess1`. `--bg` ran once.
    - M1.red: `shift-cli-handover-claims-once: a tick after the runner died mid-start ran `claude --bg` again: 2 starts; the entry is delivered.` This was the 5.183.0 `handOver`, run before the split from a scratch module that imported the validator's helpers, because `validate_plugin.py` was under keel-maint-2's split lock then. The concurrent half already passed on 5.183.0, because its lock spans the whole hand-over. The red is the dead runner: its entry stayed `pending`, and the next tick started again once the lock read as stale.
    - M1.green: `shift-cli-handover-claims-once scenario passed.` `claim` writes `starting` with `runner_pid`, `starting_at` and `attempts` under the lock, then releases it. `runnerGone` and `startedFor` settle a dead runner's claim by adopting the listed session.
    - M2: pass. `shift-cli-retries-failed-handover scenario passed.`
      - Always failing: five ticks made 3 `--bg` attempts. The entry stayed `failed`, and both `keel shift status` and `keel patrol` name `keel chat wake now verify`.
      - Failing twice: the entry was delivered as `newsess3` on the third attempt.
      - Old session idle again, or an entry with no `attempts`: 1 `--bg` attempt and still `failed` over two more ticks.
    - M2.red: `shift-cli-retries-failed-handover: five ticks ran a failing `claude --bg` 1 times, not 3.` This was the same 5.183.0 code and scratch module: `handOver` only took `pending` entries.
    - M2.green: `shift-cli-retries-failed-handover scenario passed.` `actionable` takes a `failed` entry with `attempts` below 3. `claim` declines one whose old session has a `status` again. `retryNote` names the tick's next attempt, or `keel chat wake now <role>` once none is left.
    - M3: pass.
      - The baseline exits 0.
      - `node scripts/run_python.js scripts/validate_plugin.py --group shift` reports `validation --group shift passed: 46 scenarios.` That group covers every `shift-*`, `tick-*` and `patrol-*` scenario, including `shift-cli-self-shift`, `shift-cli-keeps-old-sessions`, `shift-cli-removes-after-exit`, `shift-cli-names-host-failure`, `tick-retries-failed-wake`, and the two new ones.
      - `chat-wake-now-cli` and `chat-wake-skips-removed-session` pass.
      - `assertion-shape-count` passes at 74 sites, after one new condition was split.
      - All 10 scenario names that `docs/host-contract.md` cites are registered in `scripts/validation/registry.py` (`cited 10 missing []`).
    - Review:
      - Status: pass
      - Acceptance check:
        - M1 runs real concurrent `keel` processes and a real killed runner against the fake host, and counts `--bg` calls. That is the "never starts two sessions" behaviour of D1–D3.
        - M2 counts attempts across real ticks and reads the owner-facing status and patrol text, covering D4 and D5, including both cases where no retry is allowed.
        - The contract page rows now cite these scenarios (D6).
      - Scope check:
        - Product changes are limited to `src/core/shift.js`, `docs/host-contract.md`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `scripts/validation/shift.py`, and `scripts/validation/registry.py`. All are in Touch after the recorded reauthorization.
        - `scripts/validate_plugin.py` is unchanged by this task.
        - The rest of the diff since the fingerprint is the merge of origin/main (5.184.0).
      - Findings:
        - One new assertion guarded three failures behind one message, and `assertion-shape-count` caught it at 75 sites. It is split into three messages. Resolved here: M3
        - The desktop app path, Codex, and whether a timed-out `claude --bg` started its session remain unverified on the contract page. Durable owner: https://github.com/TanglmChris/keel/issues/408
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
    - Contract: keel-task-capsule/v1 sha256:6069f7db0cbee1b0b2c6e57b9a73da57e804a9dad68ca02e273cac5ccf7258dd (keel 5.184.0)
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
