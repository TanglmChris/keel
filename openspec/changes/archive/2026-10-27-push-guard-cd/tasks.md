# Tasks

## 1. A directory change before a push

- [x] 1.1 Deny a push preceded by `cd` or `pushd` whatever its refspec, naming `git -C <directory> push`
  - Covers:
    - keel-touch-write-guard / A push outside the declared branches is refused / A directory change before a push is refused with the -C form
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/push-guard-cd/design.md
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validation/guard.py
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validation/guard.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-guard-cd-before-push`: through the real PreToolUse hook, in a repository declaring `push:claude/*` and `push-protected:main@chief` with the session bound to no role, `cd <other repo> && git push <url> main:main` and `cd <subdir> && git push origin claude/fix` are each denied with a reason naming `git -C <directory> push` and not naming `chief`, and `git -C <other repo> push <url> main:main`, whose repository declares nothing, gets no decision. Fails with: `push-guard-cd-before-push:`
    - M2 (regression): run one at a time, each passes: `--scenario push-branch-guard`, `--scenario push-protected-guard`, `--scenario push-guard-redirects`, `--scenario push-guard-follow-tags`, `--scenario push-protected-declaration`, and `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6d70dfb2ab685ad79bfde868d2ff143025694c3e2a8b47a600736879b75966eb (keel 5.210.0)
    - M1: pass. `push-guard-cd-before-push scenario passed.` (exit 0).
    - M1.red: fail. Before the change, exit 1: ``push-guard-cd-before-push: a push in another repository after cd was denied without naming `git -C <directory> push`: 'Keel push guard: `main` is protected for role chief, and this session is bound to no chat role; only an chief session may ask to push it.'`` — the #486 misjudgement.
    - M1.green: pass. `pushTargets` returns undetermined with `form: DIRECTORY_FORM` for any push with `cdBefore`, before reading its refspec, and the `needsCurrent` special case is gone (D1). `checkPushes` denies such a push with its own reason: a `cd` or `pushd` runs before this `git push`, so the repository it pushes is unknown and this repository's push rules cannot be applied, and it names `` `git -C <directory> push <remote> <branch>` `` (D2). Other undetermined pushes keep `` `git push origin <branch>` ``. A first green attempt reused the old reason, which lists the declared entries and so named `chief`; M1 caught it, and the cd case got the reason above. `git -C <other repo> push …` still gets no decision. Literal `cd` targets are not resolved (D3).
    - M2: pass. Run one at a time, each exit 0: `push-branch-guard scenario passed.`, `push-protected-guard scenario passed.`, `push-guard-redirects scenario passed.`, `push-guard-follow-tags scenario passed.`, `push-protected-declaration scenario passed.`, `assertion-shape-count scenario passed: 74 sites`.
    - Review:
      - Status: pass
      - Acceptance check: through the real PreToolUse hook, both `cd … && git push …` forms were denied naming `git -C <directory> push` without judging them by the session repository's protected branch, and `git -C <other repo> push …` passed untouched (M1); the existing push guard scenarios still pass (M2).
      - Scope check: `git status --short` lists `plugins/keel/scripts/pretooluse-guard.js`, `scripts/validation/guard.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch.
      - Findings: Discard reason: #486's inferred miss — a session in a repository without a push scope that `cd`s into a governed one — stays unguarded. The guard governs the repository whose config it reads, and resolving `cd` targets was not taken (D3, owner's choice of the conservative fix on 2026-10-27).
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
    - openspec/specs/keel-touch-write-guard/spec.md
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
    - M2: the delta is promoted into `keel-touch-write-guard`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:881bded62546e1d90057a0e8b061d43ef7fc90cf34329542a8e8c65ad659a108 (keel 5.210.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.210.0 → 5.211.0. With the section "A push after `cd` is refused whatever its refspec, naming `git -C`" written into the stub, `version-alignment scenario passed.` (exit 0).
    - M2: the modified requirement replaces its published form in `openspec/specs/keel-touch-write-guard/spec.md`, and `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`: `validation --all passed: baseline plus 351 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.211.0, the promoted spec validates strictly, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, and this change's directory, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a directory change before a push that needs the current branch" — the requirement "A push outside the declared branches is refused" in `openspec/specs/keel-touch-write-guard/spec.md`. Updated by: 2.1.
- I2: "the directory changes before it, so its branch is unknown here" — the undetermined reason in `plugins/keel/scripts/pretooluse-guard.js`. Updated by: 1.1.

## Expectation Coverage

- E1: A `cd` or `pushd` before a push makes it undetermined whatever its refspec, and the refusal names `git -C <directory> push` (D1, D2); resolving `cd` targets is not taken (D3) (#486). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
