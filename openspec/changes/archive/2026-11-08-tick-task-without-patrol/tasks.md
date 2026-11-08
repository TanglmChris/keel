# Tasks

## 1. A job for a repository with no patrol

- [x] 1.1 Render the job without a declared patrol
  - Covers:
    - keel-coordinator-patrol / A tick job does not need a patrol / A repository with no patrol gets a job
    - keel-coordinator-patrol / A tick job does not need a patrol / An unreadable patrol is still refused
    - keel-coordinator-patrol / A tick job does not need a patrol / The job's tick carries a hand-over out with no patrol
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/tick-task-without-patrol/design.md
    - src/core/tick.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/tick.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-task-without-patrol`: in the `shift_scratch` repository, which declares no `patrol:`, `keel tick task` run from the main checkout and from a linked worktree under `.claude/worktrees/` exits 0 and prints a plist whose `--repo` and `WorkingDirectory` are the main checkout, naming no worktree, with text saying the repository declares no `patrol:` and that the job resumes ended sessions and carries hand-overs out; the printed command `keel tick --repo <main checkout>` run as printed exits 0. Fails with: `tick-task-without-patrol:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-task-refuses-unreadable-patrol`: a `patrol:` with a role and no `every:` makes `keel tick task` exit non-zero and print the config's message, and prints no plist. Detects: `an unreadable patrol is treated as no patrol` -> `tick-task-refuses-unreadable-patrol:`
    - M3 (regression): run one at a time, each passes: `--scenario tick-task-names-main-checkout`, `--scenario tick-skips-missing-bound-worktree`, `--scenario tick-runs-due-patrol`, `--scenario shift-cli-keeps-worktree-in-use` (its hand-over is carried out by `keel tick --repo` in a repository with no patrol), `--scenario assertion-shape-count`, and `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bc686f67ba188fc23c6b2b0a3683c802afef105189ccb42fb03c28e97d8074f1 (keel 5.217.0)
    - M1: pass. `tick-task-without-patrol scenario passed.` (exit 0). In the `shift_scratch` repository (it declares no `patrol:`), `keel tick task` from the main checkout and from a linked worktree under `.claude/worktrees/` exits 0, the plist's `--repo` and `WorkingDirectory` are the main checkout, no worktree is named, the text says `declares no \`patrol:\``, `resumes ended sessions`, `carries hand-overs out` and `Keel creates nothing`, and `keel tick --repo <main checkout>` exits 0.
    - M1.red: fail. Before any code change, exit 1: `tick-task-without-patrol: keel tick task failed in the main checkout with no patrol declared: 'keel tick: keel/config.yaml declares no `patrol:` with role and every.\n'`.
    - M1.green: pass. `task()` in `src/core/tick.js` separates "declares nothing and has no message" (D1), `stableRepo` takes the main checkout for it (D2), and `renderTask` says the job runs no patrol (D3).
    - M2: pass. `tick-task-refuses-unreadable-patrol scenario passed.` (exit 0), before and after the code change (which is why it is a regression check): `patrol:` with a role and no `every:` makes `keel tick task` exit non-zero with a message on stderr and no plist.
    - M2.detects: fail. With `patrolless = !declared.declarations.length;` (messages ignored), exit 1: `tick-task-refuses-unreadable-patrol: keel tick task printed a job for a patrol it cannot read: 'launchd job for `keel tick` (label dev.keel.tick.rtl): …`; the code was restored byte for byte (`cmp`) and the scenario passed again.
    - M3: pass. Run one at a time, each exit 0: `tick-task-names-main-checkout`, `tick-skips-missing-bound-worktree`, `tick-runs-due-patrol`, `shift-cli-keeps-worktree-in-use` (its hand-over is carried out by `keel tick --repo` in a repository with no patrol), `assertion-shape-count scenario passed: 74 sites, a bound on a shape and not a count of defects.`, and `validation --group shift passed: 85 scenarios.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick task` and `keel tick`, a repository with no patrol gets a job naming the main checkout and saying it runs no patrol (M1); an unreadable patrol is still refused (M2); a declared patrol's job and the tick's hand-over are unchanged (M3).
      - Scope check: `git status --short` lists `src/core/tick.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py` and this change's directory, all in Touch or the change's record layer.
      - Findings: Discard reason: `patrolless` is decided from the calling worktree's config, so a main checkout that declares a patrol the calling worktree does not still gets a job that runs it, described as running none; the text names the main checkout, and a repository whose branches differ on `patrol:` is not a case the issue raises. Durable owner: https://github.com/TanglmChris/keel/issues/509 (expectation 3, dropping Keel's own `patrol:`, is the owner's configuration choice after release).
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 State it in the docs
  - Covers:
    - D3
  - Read:
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Touch:
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: evidence-first
    - Reason: documentation prose; nothing here can fail before it is written, and 1.1 proves the behavior it describes.
    - M1: `grep -n "#509" docs/cli-team.md docs/cli-team.zh-CN.md` shows, in the tick section of each, that `keel tick task` also prints a job for a repository with no `patrol:`, which then only resumes ended sessions and carries hand-overs out, in both languages.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario surfaces-agree-with-code` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6f6256e83bb7508a9a8e67fc751b7cea7783949a9e643f50d705014f7254d5f5 (keel 5.217.0)
    - M1: pass. `grep -n "#509" docs/cli-team.md docs/cli-team.zh-CN.md` finds one hit in each, in the tick section: a repository with no `patrol:` gets the same job, whose runs resume ended sessions and carry hand-overs out and run no patrol, and an unreadable `patrol:` is still refused. The first plan grepped `declares no`, which the Chinese text does not contain; the check was corrected and the contract re-recorded before any evidence.
    - M2: pass. `surfaces-agree-with-code scenario passed.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the tick section now says a repository without a patrol gets a job that only resumes and hands over, in both languages, as 1.1 proved.
      - Scope check: `git status --short` additionally lists `docs/cli-team.md` and `docs/cli-team.zh-CN.md`, both in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - openspec/specs/keel-coordinator-patrol/spec.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - docs/host-contract.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Tasks 1.1 and 1.2 prove the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that state.
    - M2: the delta is promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:53d296203d555cbc96896ecbb7019089c046e999f9ddc81e38123908f487f34d (keel 5.217.0)
    - M1: pass. `node scripts/bump_version.js minor` moved every marker 5.219.0 → 5.220.0; the changelog entry replaced the stub. `version-alignment scenario passed.` (exit 0).
    - M2: pass. The requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`; `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`, started at load 6 with no other full run: `validation --all passed: baseline plus 372 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0, `EXIT 0` in the log), the 370 of 5.219.0 plus this change's two.
    - Review:
      - Status: pass
      - Acceptance check: the release carries tasks 1.1 and 1.2's behavior, the markers agree at 5.220.0, the promoted spec validates, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, the files of tasks 1.1 and 1.2 and this change's directory, all in Touch of 1.1, 1.2 or 2.1.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "declare the `patrol:` in the main checkout and print it again" — the fallback sentence `renderTask` prints in `src/core/tick.js`, advice that does not apply to a repository with no patrol. Updated by: 1.1.
- I2: "declares no `patrol:` with role and every" as the reason `keel tick task` fails — the failure the issue records. Updated by: 1.1.

## Expectation Coverage

- E1: `keel tick task` renders a job for a repository with no `patrol:` that does only the resume and the hand-over (#509, expectation 1; D1 to D3). Covered by: 1.1
- E2: With a declared patrol the behavior is unchanged (#509, expectation 2; D2, D4). Covered by: 1.1
- E3: The release carries it. Covered by: 2.1
- E4: Keel's own repository drops its `patrol:` (#509, expectation 3). Discard reason: the owner decided on 2026-11-08 to settle that after this lands, because the patrol still raises the disk, remote-tip and dirty-checkout alerts for keel-maint; it is a configuration choice, not a change.
