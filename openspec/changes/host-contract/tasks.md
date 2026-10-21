# Tasks

## 1. Keep the CLI hand-over and wake to the measured host contract

- [x] 1.1 Remove only exited sessions, name host failures, bound wake retries, and write the contract down
  - Covers:
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / The old session is removed only after its process exits
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / A host that cannot be listed is named
    - keel-shift-change / The CLI hand-over and wake keep to the measured host contract / A failed wake is retried a bounded number of times
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - openspec/changes/host-contract/design.md
    - src/core/shift.js
    - src/core/tick.js
    - src/core/chat/notice.js
  - Touch:
    - src/core/shift.js
    - src/core/tick.js
    - src/core/chat/notice.js
    - docs/host-contract.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-removes-after-exit`: with the old session's recorded process ending a second after `claude stop` returns, the hand-over's `claude rm` of it runs only once that process has exited; with a process that never exits (and `KEEL_SHIFT_EXIT_WAIT_MS` short), it is not removed and `keel shift status` names `claude attach` for it. Fails with: `shift-cli-removes-after-exit:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-names-host-failure`: with `KEEL_CLAUDE` naming no executable, and with a claude whose `agents --json --all` prints no list, a pending hand-off stays pending after `keel tick` and `keel shift status` names `claude was not found` and the unreadable listing respectively. Fails with: `shift-cli-names-host-failure:`
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-retries-failed-wake`: with a role's CLI session ended, a record waiting, and a claude whose `--bg --resume` fails, three ticks try the resume three times and a fourth does not; with a claude whose `agents --json --all` lacks the session, one tick reports it removed and later ticks do not try again. Fails with: `tick-retries-failed-wake:`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift`, `--scenario shift-cli-keeps-old-sessions` (its ready now names an exited process, as a real hand-over sees), `--scenario chat-wake-now-cli`, `--scenario chat-wake-skips-removed-session`, `--scenario assertion-shape-count`, and the baseline pass, and `docs/host-contract.md` names each scenario it cites as registered.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a777e512cf1f27b266ea83c9989ea7a93756aa7cfe190a8ed4d94ec2c59a290d (keel 5.181.0)
    - M1: pass. `shift-cli-removes-after-exit scenario passed.` The fake's `claude stop` returns while the process the note recorded runs for another second (`late`), and the hand-over's `claude rm` logs that process as gone. With a process that never exits (`never`, `KEEL_SHIFT_EXIT_WAIT_MS=500`), no `rm` runs and `keel shift status` names `claude attach` for the session.
    - M1.red: `shift-cli-removes-after-exit: `claude rm` of the session just handed over ran while its process was still running.` Before the change, `removeOldSessions` ran `rm` right after `stop`.
    - M1.green: `shift-cli-removes-after-exit scenario passed.` `removeOldSessions` now waits up to `KEEL_SHIFT_EXIT_WAIT_MS` (default 15 s) for the handed-over session's recorded process, and skips any other old session whose process still runs.
    - M2: pass. `shift-cli-names-host-failure scenario passed.` With `KEEL_CLAUDE` naming no file, the hand-off stays pending after `keel tick`, and status reads `pending: cannot ask the host — claude was not found; put it on PATH or name it with KEEL_CLAUDE`. With a claude whose listing prints no JSON, status names `claude agents --json --all`.
    - M2.red: `shift-cli-names-host-failure: shift status does not name why the hand-off waits (missing, expected 'claude was not found'): …`. Status only said `pending: waits for the session to go idle`.
    - M2.green: `shift-cli-names-host-failure scenario passed.` `queryAgents` returns the cause, `handOver` writes it to the entry's `waiting_on`, and `describeHandOff` and `handOffRisks` show it.
    - M3: pass. `tick-retries-failed-wake scenario passed.` With a failing resume, four ticks make 3 resume attempts. With the session missing from `agents --json --all`, there is 1 lookup and 0 resumes.
    - M3.red: `tick-retries-failed-wake: four ticks tried a failing resume 1 times, not 3.` `wakeEnded` marked the role woken after the first failed attempt.
    - M3.green: `tick-retries-failed-wake scenario passed.` `wake_attempts[role] = {record, count}`, and `woken` is set only on ok, on removed, or once count reaches 3.
    - M4: pass. The baseline exits 0 (`Keel v4.1.0 baseline validation passed.`). All 75 scenarios also pass:
      - every `chat-*`, `shift-*`, `tick-*`, `patrol-*`, and `mailbox-*` scenario, including `shift-cli-self-shift`, `shift-cli-keeps-old-sessions` (its ready now names an exited process), `chat-wake-now-cli`, `chat-wake-skips-removed-session`, and the three new ones;
      - `assertion-shape-count`, at 74 sites.
      A registry check confirmed that all 8 scenario names `docs/host-contract.md` cites are registered (`cited 8 missing []`).
    - Review:
      - Status: pass
      - Acceptance check:
        - M1 drives the real `keel shift ready --wake` and `keel tick` against a fake whose stop returns before exit, and observes the order of `rm` against the process's life. That is the D1 behavior.
        - M2 reads the owner-visible `keel shift status` for both a missing and an unreadable host (D2).
        - M3 counts real resume calls across real ticks, and distinguishes a removed session from a failing resume (D3).
        - D4 is the page, with each cited scenario checked as registered.
        - D5 (no change to the busy/waiting/idle reading) is held by the `shift-cli-self-shift` regression.
      - Scope check: the diff is confined to the five Touch files (`src/core/shift.js`, `src/core/tick.js`, `src/core/chat/notice.js`, `docs/host-contract.md`, `scripts/validate_plugin.py`) plus this change's own directory.
      - Findings:
        - The keeps-old scenario passed a still-running pid as `CLAUDE_PID`. Under D1 that would leave the session in place, so the scenario now names an exited process, as a real hand-over sees. Resolved here: M4
        - The dead `KEEL_SHIFT_RENAME_WAIT_MS` and `KEEL_SHIFT_STOP_WAIT_MS` settings in two scenarios were removed. Resolved here: M4
        - Desktop, Codex, a real waiter/tick race, and re-queueing a `failed` hand-off stay unverified, as the page states. Durable owner: https://github.com/TanglmChris/keel/issues/408
    - Blocker: none
    - Reauthorizations: none

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
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-shift-change/spec.md
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
    - M2: the delta is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
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

- I1: "pending: waits for the session to go idle" as the only pending reason — `describeHandOff` in `src/core/shift.js`. Updated by: 1.1.
- I2: "A blocked AskUserQuestion reports `status: idle`, `state: working`" — the archived cli-shift-handover design F1, superseded by this change's F1 and `docs/host-contract.md`. Discard reason: archived designs record what was measured then and are not rewritten; the contract page states the current measurement.

## Expectation Coverage

- E1: On the CLI path, a hand-over never removes a running session, a host it cannot read is named, a failed wake is retried within a bound, and the contract with its evidence is written down (#408; D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Follow-ups

- The Desktop and Codex paths, a real concurrent race between waiter and tick, and a re-queue for a `failed` hand-off are out of this first loop; `docs/host-contract.md` lists them as unverified. Durable owner: https://github.com/TanglmChris/keel/issues/408
