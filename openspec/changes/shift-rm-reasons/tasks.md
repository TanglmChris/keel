# Tasks

## 1. Old sessions: never a worktree in use, always a reason

- [x] 1.1 Keep a session whose worktree is in use, record why each old session stayed, and say so in `keel shift status`
  - Covers:
    - keel-shift-change / A hand-over never removes a worktree in use, and says why an old session stayed / An old session whose worktree the new shift uses stays, and status says why
    - keel-shift-change / A hand-over never removes a worktree in use, and says why an old session stayed / A failed removal is reported with the host's message
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - openspec/changes/shift-rm-reasons/design.md
    - src/core/shift.js
    - scripts/validation/shift.py
    - docs/host-contract.md
  - Touch:
    - src/core/shift.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - docs/host-contract.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-worktree-in-use`: with the fake `claude` of `HANDOVER_CONTRACT_FAKE`, a session `5b14fbae` whose row `cwd` is rtl's worktree and whose `<config>/jobs/5b14fbae/state.json` names verify's worktree as `worktreePath` runs the real `keel shift ready --wake` in verify's worktree, and the real `keel tick` delivers the hand-off; the fake logs no `rm 5b14fbae`, and the real `keel shift status` contains `not removed`, verify's worktree path, `claude rm would delete it`, and `claude attach 5b14fbae`, and not `old session kept`. Fails with: `shift-cli-keeps-worktree-in-use:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-names-failed-removal`: with the same fake and `FAKE_RM_FAIL=worktree has unpushed commits`, a hand-over from verify's worktree of a session whose row `cwd` is verify's worktree leaves `keel shift status` containing `not removed`, `claude rm exited 1`, and `worktree has unpushed commits`, and not `old session kept`. Fails with: `shift-cli-names-failed-removal:`
    - M3 (regression): run one at a time, each passes: `--scenario shift-cli-removes-after-exit`, `--scenario shift-cli-keeps-old-sessions`, `--scenario assertion-shape-count`, `--scenario surfaces-agree-with-code`, and `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cdce66286ccbb7cd6bc5b53ec66d4d4cd442848fbbece2ff23775d234a5c4a7f (keel 5.213.0)
    - M1: pass. `shift-cli-keeps-worktree-in-use scenario passed.` (exit 0).
    - M1.red: fail. Before the change, exit 1: ``shift-cli-keeps-worktree-in-use: shift status does not name 'not removed': '… - verify: delivered … as session newsess1 "verify · 10-28 08:31"; requested …; old sess…'`` — the session was skipped silently and status used the keep sentence.
    - M1.green: pass. The session the entry names is a candidate whatever its row's `cwd`, and its transcript is also looked for under the worktree the host records for it (D1). `hostWorktree` reads `<config>/jobs/<id>/state.json` `worktreePath`; when that directory is the entry's worktree, a bound one, or another listed session's `cwd`, the session is not removed, with the reason (D2). The fake logged no `rm 5b14fbae`, and status read ``old session not removed: its worktree …/verify is in use (the new shift's worktree), and claude rm would delete it; it stays in `claude agents`, and opening it (`claude attach 5b14fbae`) brings it back beside the new shift`` (D4).
    - M2: pass. `shift-cli-names-failed-removal scenario passed.` (exit 0).
    - M2.red: fail. Before the change, exit 1: ``shift-cli-names-failed-removal: shift status does not name 'not removed': '… - verify: delivered … as session newsess1 "verify · 10-28 08:31"; requested …; old sessi…'`` — a failed `claude rm` read as kept.
    - M2.green: pass. `removeOldSessions` returns `{ removed, notRemoved }` and records, for each session left, kept by `keep_old_sessions`, still running, transcript not copied, worktree in use, or `claude rm exited <n>: <first stderr line>`; `deliver` stores it as `not_removed`, and resume keeps using `removed` (D3). Status named `claude rm exited 1: worktree has unpushed commits`.
    - M3: pass. Run one at a time, each exit 0: `shift-cli-removes-after-exit scenario passed.` (its never-exits case now reads "not removed: its process was still running" and still names `claude attach`), `shift-cli-keeps-old-sessions scenario passed.`, `assertion-shape-count scenario passed: 74 sites`, `surfaces-agree-with-code scenario passed.`, and `validation --group shift passed: 69 scenarios.`. `docs/cli-team.md` (+ zh-CN) and `docs/host-contract.md` say what a session that created its worktree does and how status names a session left listed (I2, I3).
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift ready --wake`, `keel tick`, and `keel shift status` against the contract fake, a session whose host-recorded worktree is the new shift's was not `claude rm`'d and status named why and that opening it revives it (M1); a failed `claude rm` was reported with its exit status and message rather than as kept (M2); the existing hand-over and retention scenarios pass (M3).
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `docs/host-contract.md`, and this change's directory, all in Touch.
      - Findings: Discard reason: dropping a listed session while keeping its worktree was not built, because no measured host command does it (`claude rm --help` on 2.1.311 offers only forcing the deletion); a session left for a worktree in use goes at a later hand-over once nothing uses that worktree (D5).
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

- I1: "old session kept, reopen it with `claude attach`" — `describeHandOff` in `src/core/shift.js`, printed for any old session not removed. Updated by: 1.1.
- I2: "`claude rm` of a session started in an existing worktree leaves the worktree in place." — `docs/cli-team.md` and its counterpart in `docs/cli-team.zh-CN.md`, which say nothing of a session that created its worktree, or of an old session left with a reason. Updated by: 1.1.
- I3: "A session whose process still runs is never removed and stays listed." — `docs/host-contract.md`, whose table has no row for a session that created its worktree. Updated by: 1.1.
- I4: "remove each older one with `claude rm` only once Keel's store holds a copy of its transcript, recording the removed ids on the entry" — the requirement "A CLI session changes its own shift and the next one is named for its start" in `openspec/specs/keel-shift-change/spec.md`. Discard reason: still true; the added requirement states the worktree check and the recorded reasons beside it, promoted by 2.1.

## Expectation Coverage

- E1: A hand-over never deletes a worktree in use and records why each old session stayed; status says so instead of calling it kept (D1–D4); dropping a session while keeping its worktree is not available on the host (D5) (#492). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
