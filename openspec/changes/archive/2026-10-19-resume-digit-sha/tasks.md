# Tasks

## 1. An all-digit sha is still a commit

- [x] 1.1 Accept any hex after `@`, and a bare all-digit token that resolves
  - Covers:
    - keel-shift-change / A resumed note's commits are checked against the remote / An all-digit sha is still a commit
    - D1
  - Read:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-checks-commits` additionally searches commit-tree for a commit whose first eight characters are all digits, points `digits-branch` at it on the real bare remote, and has the real `keel shift resume` mark `digits-branch @ <digits>` current and list the bare `<digits>`, while `20261018` stays unlisted. Fails with: `an all-digit sha after `
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:691621950160d51de6fac7b5ff28364a162e9016d9a39e3f322ab94d10845649 (keel 5.152.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-checks-commits` reports `shift-resume-checks-commits scenario passed.`
    - M1.red: fail. With the all-digit case added and `shift.js` unchanged: `shift-resume-checks-commits: an all-digit sha after `@` is not marked current: '' in [...]`, carrying the declared signature; the same skip is what CI run 39211624782 hit at random with `feat @ 02607471`.
    - M1.green: pass. With a pair's sha taken as any hex and a bare all-digit token listed only when it resolves to a commit, the scenario passed, `20261018` still unlisted.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 296 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the scenario searches for a commit whose 8-character prefix is all digits, so the case is exercised on every run rather than 2% of them; the real resume marks `digits-branch @ <digits>` current and lists the bare `<digits>`, and the date stays out.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Resolved here: M1 — the scenario was flaky because its random fixture shas sometimes hit the defect; it now exercises the all-digit case deterministically.
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
    - Contract: keel-task-capsule/v1 sha256:037f583ad743ed0ae83193569bbf51291ea396986bf5798b3c9d5ede62486e2b (keel 5.152.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.153.0 → 5.154.0; with the "An all-digit sha a note names is still a commit" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a commit id being 7 to 40 hex digits holding at least one letter and one digit" — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: Every sha a note names is checked, including the 2% that are all digits, without listing dates (D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
