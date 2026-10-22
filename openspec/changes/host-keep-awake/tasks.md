# Tasks

## 1. The host's keep-awake

- [x] 1.1 Leave the host's own `caffeinate` out of `keel shift check`, and stop prescribing `--force-reason` for it
  - Covers:
    - keel-shift-change / The readiness check reports what would be lost or left running / The host's keep-awake is not a loose end
    - keel-shift-change / The readiness check reports what would be lost or left running / Each kind of loose end is reported
    - keel-shift-change / A session changes its own shift with one slash command / The command's own steps hand a shift over
    - D1
    - D2
  - Read:
    - openspec/changes/host-keep-awake/design.md
    - src/core/shift.js
    - plugins/keel/commands/shift.md
  - Touch:
    - src/core/shift.js
    - plugins/keel/commands/shift.md
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-check-skips-host-keep-awake`: in an otherwise clean worktree, a stand-in `caffeinate` (a copy of `sleep`) started by the scenario process — an ancestor of the `keel shift check` it runs — is not named, while an orphaned stand-in `caffeinate` and a `sleep` started in the worktree are named; with only the first left running, `keel shift check` exits 0. Fails with: `shift-check-skips-host-keep-awake:` Detects: `drop the caffeinate exclusion in liveProcesses` -> `names the host's own keep-awake`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes (`shift-change`, `shift-slash-command`, `self-shift-authorization`, `memory-rule-reaches-every-repo` among them), and so do `--scenario docs-zh-match-english` and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9afa324dcf6ba77084818f3211f7f5a8cef0d7fb611789f311932f3c60ee5d6c (keel 5.195.0)
    - M1: pass. `shift-check-skips-host-keep-awake scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `shift-check-skips-host-keep-awake: keel shift check names the host's own keep-awake: … - process: PID 40004, running 00:00: caffeinate 90` (exit 1).
    - M1.green: pass. `liveProcesses` skips a row matching `HOST_KEEP_AWAKE` (`caffeinate` as the program) whose parent is an ancestor of the checker, other than init (D1).
      - Leaving init out was found by this check. An orphaned stand-in is re-parented to PID 1, which is every process's ancestor, so the first green attempt skipped the orphan too.
      - The stand-ins are `exec -a caffeinate sleep N`, because macOS SIGKILLs a copied `/bin/sleep` (exit 137 when run directly).
      - Measured on the real host: in this worktree, `keel shift check` from 5.195.0 lists `PID 37350 … caffeinate -i -t 300`, and this branch's `node bin/keel.js shift check` does not.
    - M1.detects: with the skip line in `liveProcesses` replaced by a comment, the scenario failed: `shift-check-skips-host-keep-awake: keel shift check names the host's own keep-awake` (exit 1). Restored, it passes (exit 0).
    - M2: pass. `validation --group shift passed: 56 scenarios.` (exit 0), with `shift-change`, `shift-slash-command`, `self-shift-authorization`, and `memory-rule-reaches-every-repo` among them. `docs-zh-match-english` passed, and `assertion-shape-count` passed at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift check`, the host's keep-awake is left out, while an orphaned `caffeinate` and a `sleep` are still named. With only the host's keep-awake left, the check exits 0, so no `--force-reason` is needed. `/keel:shift` and both docs no longer tell the session to force past it (D2).
      - Scope check: `git status --short` lists the six Touch files and this change's directory.
      - Findings: none.
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:83bd94bfc22479c4abec2c46f8e35adb3188be519577745e414c994ba265f572 (keel 5.195.0)
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "A keep-awake the host started under this session, such as `caffeinate -i -t 300`, ends by itself, so it may stay." and "When step 1 listed only the host's own processes, add `--force-reason`" — `plugins/keel/commands/shift.md`. Updated by: 1.1.
- I2: "a keep-awake process the host started under the session, such as `caffeinate`, is not a loose end of yours" — `docs/shift-change.md`, and "宿主在会话下面启动的保持唤醒进程，例如 `caffeinate`，不算你自己的遗留" in `docs/shift-change.zh-CN.md`. Updated by: 1.1.
- I3: "to let the first stay with `--force-reason` naming it" — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: A CLI shift with only the host's keep-awake running passes `keel shift check` without `--force-reason`, while any process the session started is still reported (#447; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
