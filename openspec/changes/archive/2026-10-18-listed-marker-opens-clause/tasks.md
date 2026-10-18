# Tasks

## 1. A listed marker opens its clause

- [x] 1.1 Accept a list bullet as a clause opening for disposition markers
  - Covers:
    - keel-expectation-slice-evidence-gates / A disposition marker is recognized only where it opens its clause / A disposition written as a sub-list item parses
    - D1
    - D2
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario a-listed-marker-opens-its-clause` runs the real `keel gate task-start --record` and `task-complete` on tasks whose `Findings` is a sub-list: `Resolved here: M1` (a declared check), `Resolved here: flow/Makefile` (an existing path), the same path followed by a Chinese sentence, and two items with a `Discard reason:` each pass; `Resolved here: M9` is refused naming `M9`; `Not resolved here: … Durable owner: https://…` passes. Fails with: `is not read as a disposition (check)`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-negation-is-not-a-marker` still passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5fb00fa90934043081cb31d1ce1f85403e14038922ae9384abf0dc2788593d08 (keel 5.145.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-listed-marker-opens-its-clause` reports `a-listed-marker-opens-its-clause scenario passed.`
    - M1.red: fail. With the scenario written first and `gates.js` unchanged: `a-listed-marker-opens-its-clause: a sub-list ['Resolved here: M1'] is not read as a disposition (check); ['finding-owner'] "Review Findings must be `none` or carry a disposition …"`, carrying the declared signature `is not read as a disposition (check)` and reproducing #362's refusal.
    - M1.green: pass. With `CLAUSE_OPENING` accepting one optional `-`/`*`/`+` bullet after its openings, and the refusal naming the bullet of a list item, the scenario passed, including the path followed by a Chinese sentence.
    - M2: pass. `--scenario a-negation-is-not-a-marker` reports `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 290 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `task-start --record` and `task-complete` on sub-list Findings: a declared check, an existing path, the path with a Chinese sentence after it, and a check plus a discard each complete; an undeclared `M9` is refused naming it; a listed negation with a durable owner completes.
      - Scope check: `git status --short` lists `src/core/gates.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the reporter's other change passed with a prose `Resolved here:` beside a `Durable owner:` because `findingOwnerIsDurable` reads owner markers without the opening rule; with listed markers now recognized, that prose `Resolved here:` is held to the resolution-evidence rule, so such a mixed entry may now be refused for its evidence — the intended reading of a resolution claim, not a regression.
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
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
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
    - M2: the MODIFIED requirement replaces its counterpart in `keel-expectation-slice-evidence-gates`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c67cf1aa15ac326f07e7afbdb575dcd3244c5177b4b92d0f10f17f0bd141a771 (keel 5.145.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.145.0 → 5.146.0; with the "A disposition written as a sub-list item is read as one" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its counterpart in `keel-expectation-slice-evidence-gates`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section (which names the consequence for live changes) and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "preceded by the start of the value, a line break, or sentence-ending punctuation" with no list item — `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`. Updated by: 2.1
- I2: "A marker counts only where it opens its clause — after the start of the value, a line break, or sentence-ending punctuation." — the `finding-owner` refusal in `src/core/gates.js`. Updated by: 1.1
- I3: "the start of the value, a line break, or sentence-ending punctuation may precede it" — the `CLAUSE_OPENING` comment in `src/core/gates.js`. Updated by: 1.1

## Expectation Coverage

- E1: A Findings disposition written as a sub-list item is judged exactly as on the label's line (#362, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
