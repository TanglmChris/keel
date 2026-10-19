# Tasks

## 1. The CLI hand-over is prompt and retires the old session

- [x] 1.1 Leave a hand-over waiter, wait for a finished session, retire the old one by name
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The waker hands a CLI shift over once the old session is idle
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The tick and the waiter start one session
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / A rename that does not show does not stop the hand-over
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / A failed hand-off is a risk
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/shift.js
    - src/core/tick.js
    - docs/cli-team.md
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` runs `keel shift ready --wake` as CLI session `5b14fbae-…` with a fake `claude` whose `agents --json --all` answers with the measured row shapes, and no `keel tick`: with the session busy, then idle with state `working`, nothing is stopped or started; once it is idle with state `done` the fake sees, in order, `stop 5b14fbae`, `--bg --resume <full id> /rename verify · shifted …`, `stop 5b14fbae`, and `--bg -n verify --permission-mode auto …`, none of them with a `CLAUDE*` variable in its environment; a fresh `queue/verify.lock` makes a tick start nothing until it is removed; a rename that never shows still delivers and status says so; a failed start is still a patrol risk. Fails with: `the waiter did not hand over without a tick`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d198663e112534715c20cada6bf081e1914ffb519f48a10a35eba9260e4787da (keel 5.161.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`
    - M1.red: fail. With the scenario rewritten first and the code unchanged: `shift-cli-self-shift: the waiter did not hand over without a tick: []`, carrying the declared signature.
    - M1.green: pass. With `ready --wake` leaving a detached `handover-wait` waiter (cwd `/`, no `CLAUDE*` variable), the finished-session test (busy, or idle with state `working`, waits), the retire sequence, the per-role lock and the rename note in status, the scenario passed: busy and blocked-on-a-question sessions were left alone, a done one got `stop`, `--bg --resume <id> "/rename verify · shifted …"`, `stop`, `--bg -n verify …` in that order with no tick, a held lock kept the tick off, a rename that never showed still delivered with `rename not shown` in status, and a failed start stayed a patrol risk.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 303 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift ready`, `keel tick`, `keel shift status` and `keel patrol` with a fake `claude` returning the measured row shapes, the old session is retired and the new one started within a poll interval of its finishing, without a tick, never while it is busy or blocked on a question, once per entry.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `docs/shift-change.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/388 — a stale hand-off whose old session is `done` but whose waiter died waits for a tick, and a repository with neither is only reported by the patrol after 15 minutes; the real-`claude` path (`--bg --resume … /rename`) was measured on a throwaway session, not run end to end by the scenario's fake.
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
    - M2: the delta requirements are promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5dc742000f51675f25d2db12ce01661fc7ce20c5d258a8611995dbca6b372640 (keel 5.161.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.161.0 → 5.162.0; with the "A CLI shift change is prompt, waits for a finished session, and renames the old one" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "stops it once idle and starts the next" — the comment above `queueHandOff` and the sentences in `docs/cli-team.md` and `docs/shift-change.md` that say `keel tick` carries out a CLI hand-off ("On its next run after that, `keel tick` looks the session up", "`keel tick` replaces the session", "instead of leaving a waiter"). Updated by: 1.1.
- I2: "say that `keel tick` hands over once the session is idle" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: A CLI shift change is carried out within seconds of the session finishing, in any repository, without cutting off a session that waits on the owner, and the old session is left stopped under a name that says it shifted (#388; D1, D2, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
