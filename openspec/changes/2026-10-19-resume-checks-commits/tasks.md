# Tasks

## 1. A resumed note's commits are checked

- [x] 1.1 List and mark the commits a resumed note names
  - Covers:
    - keel-shift-change / A resumed note's commits are checked against the remote / A stale note's commits are marked
    - D1
    - D2
    - D3
  - Read:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-checks-commits` pushes a commit to the default branch and moves `feat` past an older tip on a real bare remote, has `verify` file a note naming them, `gone-branch @ <sha>`, `deadbee1` and `20261018`, and runs the real `keel shift resume`: the four are marked `already in origin/<default>`, `branch moved: now <new>`, `branch gone` and `not found`, the date is not listed, and the output says `not fetched`. Fails with: `is not marked 'already in origin/`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d4ab8da9c9a4f7bf6b2fdf2b7517b508d43bcca475b60587ed80723512647b70 (keel 5.149.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-checks-commits` reports `shift-resume-checks-commits scenario passed.`
    - M1.red: fail. With the scenario written first and `shift.js` unchanged: `shift-resume-checks-commits: '4eaf3c0e' is not marked 'already in origin/main': ''`, carrying the declared signature.
    - M1.green: pass. With `noteCommits` reading `<branch> @ <sha>` pairs and bare 7–40 hex ids that hold a letter and a digit, marking each against `refs/remotes/origin/*` and the remote default branch, and `resume` printing the list with the last fetch time, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 295 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: on a real bare remote, the real `keel shift resume` marks a pushed commit `already in origin/main`, `feat @ <old>` `branch moved: now <new>`, `gone-branch @ <sha>` `branch gone` and `deadbee1` `not found`, lists nothing for `20261018`, and says the refs were `not fetched`.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the check reads refs as of the last fetch rather than fetching, per Keel's rule that it fetches nothing (D2 in design); a stale fetch can still mark a merged commit as unmerged, which the printed fetch time makes visible.
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
    - M2: the delta requirements are promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A new shift sees which commits its note names are already merged, moved or missing before acting on them (#347, D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
