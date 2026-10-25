# Tasks

## 1. Remove old sessions at resume too

- [x] 1.1 Resume removes the role's old sessions, and a session Keel keeps under the role is the role's wherever it ran
  - Covers:
    - keel-shift-change / Resuming a CLI shift removes its old sessions / A hand-opened session's resume removes the old shift
    - keel-shift-change / Resuming a CLI shift removes its old sessions / Resume asks the host only when it may remove something
    - keel-shift-change / A CLI session changes its own shift and the next one is named for its start / An old session from before a worktree moved is still the role's
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/shift-resume-removes-old/design.md
    - src/core/shift.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/shift.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-removes-old-sessions`: with a stand-in claude, a note written by verify's CLI session whose process has exited, and nothing declared, the real `keel shift resume` in a new CLI session removes the handed-over session and an older verify session whose working directory is missing but whose transcript Keel keeps under `verify`, each only after Keel's copy exists; rtl's stopped session and the current session stay; the output names both ids and `keel shift history verify --show`. Resumed with no Claude Code variables, and in the session a delivered hand-off started, it makes no `claude` call and still prints the note. Fails with: `shift-resume-removes-old-sessions: resume removed no old session`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions`: a hand-over also removes a stopped session in a missing directory whose transcript Keel keeps under `verify`, and keeps one in a missing directory kept under no role. Fails with: `shift-cli-keeps-old-sessions: a session of verify's from a missing worktree stayed`
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes, and so do `--scenario docs-zh-match-english` and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b81488c44c77f5f460903df183ed2064d566270e982c5329f22b764ec7b88d2e (keel 5.198.0)
    - M1: pass. `shift-resume-removes-old-sessions scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `shift-resume-removes-old-sessions: resume removed no old session: ''` (exit 1). `resume` made no host call at all.
    - M1.green: pass.
      - `removeAtResume` reads `CLI session:` and `CLI process:` from the printed note and calls `removeOldSessions` with the current session's job id as the new one, under the declared `keep_old_sessions` (D1).
      - It returns before any host call when `CLAUDE_CODE_ENTRYPOINT` is unset, or when the role's queue entry is `delivered` to the current session.
      - `resume` prints `Removed old sessions from claude agents: …` naming `keel shift history <role> --show <id>`, and returns `removed` (D3).
    - M2: pass. `shift-cli-keeps-old-sessions scenario passed.` (exit 0).
    - M2.red: fail. Before the change: `shift-cli-keeps-old-sessions: a session of verify's from a missing worktree stayed, or another was removed: ['01010101', '02020202', '04040404', '5b14fbae']` (exit 1).
    - M2.green: pass. `removeOldSessions` counts a row as the role's when its `cwd` is bound or `keptFile(where, role, <id>.jsonl)` exists (D2). The row kept under no role stays. At review, the red's combined condition was split so each failure has its own message, and the scenario passed again.
    - M3: pass. `validation --group shift passed: 59 scenarios.` (exit 0). `docs-zh-match-english scenario passed.` `assertion-shape-count scenario passed: 74 sites`. Its first run counted 77, because three new checks each combined two failures under one message. Each now has its own message.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift resume` with a stand-in claude, a hand-opened session's resume removes the shift handed over and a pre-rename session Keel keeps under the role, each after Keel's copy exists. rtl's session and the current one stay, and the output names both ids and how to read them. Outside a Claude Code host, and after a delivered hand-over, resume makes no host call and still prints the note.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch. `.DS_Store` is untracked Finder metadata that predates the change.
      - Findings: the real host's leftovers (kaiwu-ip's pre-5.178.0 pairs, keel-maint `6fffda34`) leave only at each role's next resume in a Claude Code session, not at release. Discard reason: owner-chosen scope (#462, "两类合成一个"); a sweep across roles is rejected in design D4.
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
    - Contract: keel-task-capsule/v1 sha256:d3f98a546a719cb5577280da074de1439ce0f232a658a46aba08fa4f74a3c78a (keel 5.198.0)
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

- I1: "stopped background sessions whose working directory is one of the role's bound worktrees" — `keel-shift-change`. Updated by: 1.1, 2.1.
- I2: "the newest `keep` stopped background sessions in the role's bound worktrees stay listed" — the `removeOldSessions` comment in `src/core/shift.js`. Updated by: 1.1.
- I3: "After a hand-over, the newest `keep_old_sessions` of the role's stopped sessions stay listed" and "交接之后，该角色最新的 `keep_old_sessions` 个已停会话留在列表里" — `docs/cli-team.md` and `docs/cli-team.zh-CN.md`, which name no removal at resume. Updated by: 1.1.

## Expectation Coverage

- E1: A shift change leaves no old session listed by default, whether Keel carried the hand-over out or a session opened by hand resumed the note, and a renamed or moved worktree does not strand old sessions (#462; D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
