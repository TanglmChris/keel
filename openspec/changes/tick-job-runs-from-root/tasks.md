# Tasks

## 1. The job

- [x] 1.1 The printed tick job runs from `/`
  - Covers:
    - keel-coordinator-patrol / A host-run tick runs the patrol when due / The launchd job is printed, not installed
    - keel-coordinator-patrol / A host-run tick runs the patrol when due / A job printed from a worktree names the main checkout
    - keel-coordinator-patrol / A tick job does not need a patrol / A repository with no patrol gets a job
    - D1
    - D2
  - Read:
    - openspec/changes/tick-job-runs-from-root/design.md
    - src/core/tick.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/tick.js
    - scripts/validation/shift.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-task-names-main-checkout` and `--scenario tick-task-without-patrol`: the plist `keel tick task` prints from the main checkout and from a linked worktree names the main checkout after `--repo` and `/` as `WorkingDirectory`, still carries `StartInterval` 300, `tick`, `launchctl bootstrap` and `Keel creates nothing`, and names no worktree. Fails with: `does not name the main checkout`
    - M2 (regression): run one at a time, each passes: `--scenario launchd-doctor-names-job-directories`, `--scenario launchd-stable-node`, `--scenario tick-skips-missing-bound-worktree`, `--scenario tick-task-refuses-unreadable-patrol`, `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1094b5d1f363dea6ec6280bfa3e7d1a9f799abeaa2d187a49f946ced185b6c9c (keel 5.227.0)
    - M1: pass. `tick-task-names-main-checkout scenario passed.` and `tick-task-without-patrol scenario passed.` (exit 0 each). The plist `keel tick task` prints from the main checkout and from a linked worktree names the main checkout after `--repo` and `/` as `WorkingDirectory`, with `StartInterval` 300, `tick`, `launchctl bootstrap` and `Keel creates nothing`, and names no worktree; the text now says the job runs for the main checkout and from the filesystem root.
    - M1.red: fail. With the scenarios updated to expect `/` and no code change, exit 1: `tick-task-names-main-checkout: the job printed from a worktree does not name the main checkout '/private/var/folders/…/rtl' after --repo and / as WorkingDirectory: --repo '/…`, and the same for `tick-task-without-patrol`.
    - M1.green: pass. `task()` in `src/core/tick.js` writes `WorkingDirectory` as the root of the repository path, `renderTask` says `for` the checkout and adds that the job runs from the root, and both `docs/cli-team*.md` say so (D1, D2).
    - M2: pass. Run one at a time (load 12.6 at the first), each exit 0: `launchd-doctor-names-job-directories`, `launchd-stable-node`, `tick-skips-missing-bound-worktree`, `tick-task-refuses-unreadable-patrol`, `surfaces-agree-with-code`, and `assertion-shape-count scenario passed: 74 sites, a bound on a shape and not a count of defects.`
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick task`, the printed job names the repository after `--repo` and runs from `/` in every case the spec lists (main checkout, worktree, no patrol), and the doctor's job-directory check still accepts such a plist (M1, M2).
      - Scope check: `git status --short` lists `src/core/tick.js`, `scripts/validation/shift.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings: Discard reason: the tick's real children were not run from `/` in a scenario; the design records why none depends on its cwd (each names its directory, and `claude agents --json --all` returned the same 29 rows from `/` and the checkout when probed); the full suite in 2.1 runs every tick scenario.
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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
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
    - openspec/specs/keel-coordinator-patrol/spec.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that state.
    - M2: the delta is promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6e37a1cccd8bbaffc8e62e332992332fff1b744dc183befb30cfb4f0884e20e1 (keel 5.227.0)
    - M1: pass (2026-11-16). Resumed the existing 5.227.0 -> 5.228.0 version bump without incrementing it again; the diff against 8e490e82 carries aligned package, lock, marketplace, plugin, protocol and validator markers. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` exits 0 on Linux and Mac: `version-alignment scenario passed.`
    - M2: pass (2026-11-16). The two modified requirements and their scenarios match the delta in the published `keel-coordinator-patrol` spec. On Mac, with the existing lockfile-matching OpenSpec 1.14.0, `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` exits 0: `35 published specs validate strictly against openspec 1.14.0`. Linux's scenario reported its missing-local-dependency skip, so that result is not counted as this proof; an additional `keel openspec validate --specs --strict` there passed 35/35 using the installed CLI dependency.
    - M3: pass (2026-11-16). On Mac's unchanged candidate product files, `npm test -- --jobs 2` exits 0: `validation --all passed: baseline plus 398 scenarios, 1 skipped: output-survives-the-pipe.` Evidence classification: 254 deterministic, 144 against a stand-in host, none on a real host. The macOS pipe-size scenario is the named platform skip; both native plugin scenarios passed. Log: `/tmp/keel-5.228.0-full-test.log` on Mac. Linux startup initially returned 127 because restricted Node spawning reported EPERM for the installed Python 3.10.12; the same targeted checks ran normally with standard process permissions. No dependencies were installed and no check was weakened.
    - Review:
      - Status: pass
      - Acceptance check: the 5.228.0 release markers agree (M1), both modified published requirements and their scenarios match the delta and all 35 specs validate strictly (M2), and the complete existing suite passes including the public tick-task behavior scenarios and native plugin probes (M3). Linux also re-ran the two tick-task scenarios successfully. Existing plists are deliberately not rewritten, as E3 and the changelog state.
      - Scope check: relative to 8e490e82, product changes are the union of 1.1 and 2.1 Touch. This resumed task changed only its own task records; all inherited product bytes were preserved. Compared the Linux and Mac candidate product files before testing; the original 29 changed files matched byte-for-byte. No host task or installed CLI/plugin was changed. Checked project memory by the WorkingDirectory/tick-checkout symptom on both hosts; no invalidated claim was found.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 3. Reviewable release candidate

- [ ] 3.1 Commit the verified 5.228.0 release candidate
  - Mode: repo-action
  - Covers:
    - E2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: this commits the verified release snapshot; it introduces no new behavior.
    - M1: `git log -1 --format=%s` identifies the 5.228.0 tick working-directory repair for #524, and `git show --stat HEAD` includes the implementation, version markers, published spec and task evidence.
    - M2: `git diff --exit-code HEAD -- src/core/tick.js scripts/validation/shift.py package.json npm-shrinkwrap.json openspec/specs/keel-coordinator-patrol/spec.md` proves the verified product snapshot is committed.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bb5433fd52865ad752be5b160c50f73be48d641a39f449555e078149a05542de (keel 5.227.0)
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "in the main checkout" as where the job runs — `docs/cli-team.md` and `docs/cli-team.zh-CN.md` say the plist calls `keel tick` every 300 seconds in the repository's main checkout, and `renderTask` in `src/core/tick.js` prints the same. Updated by: 1.1.
- I2: "name the repository's main checkout as `--repo` and as `WorkingDirectory`" and the two scenarios that repeat it — the requirements of `keel-coordinator-patrol` this change modifies. Updated by: 2.1.

## Expectation Coverage

- E1: The tick job no longer has its cwd inside the main checkout (#524; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: An already-installed plist keeps working until the owner re-installs it (#524 does not ask Keel to rewrite it; Keel registers nothing). Discard reason: the owner's rule that Keel never touches LaunchAgents or launchctl; the changelog tells the owner to re-run `keel tick task` and its install commands.
