# Tasks

## 1. Unbound self-shift

- [x] 1.1 `ready` in an unbound worktree needs a role and `--wake`, or a stated reason
  - Covers:
    - keel-shift-change / The outgoing shift leaves a note and closes the request / A worktree without a chat role is pointed to a role and --wake
    - keel-shift-change / The outgoing shift leaves a note and closes the request / A worktree without a chat role changes shift by hand
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` follows the scenario: in a worktree with no chat role, plain `keel shift ready "next: rerun R007"` exits 1 naming `keel chat role --set` and `--wake` and stores no note; `keel shift ready --force-reason "the owner opens it" "next: rerun R007"` stores a worktree note containing `Started by hand: the owner opens it` and prints a hint naming `the owner opens it`; `keel context` and the SessionStart projection then name `keel shift resume`, which consumes it; and both shift-change docs name `--wake` beside the optional chat role. Fails with: `shift-without-role:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:359d44daf952776921cfacf1a7f742450d75475ae0dc457fa9477f0334018b8e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` reports `shift-without-role scenario passed.`
    - M1.red: fail. With the scenario rewritten first, it reported `shift-without-role: plain ready in a worktree without a chat role was not refused naming a role and --wake: exit 0: Stored the shift note for this worktree …`, carrying the declared signature `shift-without-role:`.
    - M1.green: pass. With the refusal before the readiness check, the `Started by hand:` line, and the clear hint naming the reason: plain `ready` exits 1 naming `keel chat role --set` and `--wake` and stores no note; `--force-reason "the owner opens it"` stores a note recording `Started by hand: the owner opens it` and a hint naming it; `keel context` and the SessionStart projection name `keel shift resume`, which consumes it; both docs name `--wake` and `--force-reason` in their intro.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel shift ready` in a temporary repository with no chat role, reads its exit code, stderr, stdout, and the stored note, then drives `keel context`, the SessionStart hook, and `keel shift resume`.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, and this change's own directory. The first full run failed `shift-role-elsewhere`, which filed an unbound self-shift without a reason, and `assertion-shape-count`, which counted a combined guard in the new assertions; the first now passes `--force-reason`, and the guards are split.
      - Findings: Resolved here: M1 — review found an unbound note filed with `--force-reason` and a clean check carried an empty `Left as is (…):` block, reading as loose ends left behind; the block now appears only when the check found items, and M1 asserts its absence.
        Discard reason: a bound role with no open request that runs `ready` without `--wake` still clears with nobody set to start it; the owner's decision on #317 named the unbound case only, and that bound case's hint already names `--wake`.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3daa4f5c624783bd38bcaf815de869ab1763295715c6b7ee88ab6138a7339d2e
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.126.0; with the 5.126.0 changelog section written into the stub's place, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the promoted spec are checked by the two scenarios, and the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "With no chat role, a shift change still works. `check`, `ready`, and `resume` need nothing but the repository." — `docs/shift-change.md` intro, and its translation "不绑定聊天角色也能换班：`check`、`ready`、`resume` 只需要仓库本身" in `docs/shift-change.zh-CN.md`. Updated by: 1.1
- I2: "MUST NOT require a chat role" — `openspec/specs/keel-shift-change/spec.md`, The outgoing shift leaves a note and closes the request. Updated by: 2.1
- I3: "Without a chat role, tell the new session to run `keel shift resume`." — the clear hint in `src/core/shift.js`. Updated by: 1.1

## Expectation Coverage

- E1: A session changing its own shift from a worktree bound to no role cannot clear without either an armed wake or a stated person who starts the new session (D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.126.0 tree reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`
