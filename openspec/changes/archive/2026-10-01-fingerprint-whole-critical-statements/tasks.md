# Tasks

## 1. Bind cited critical authority to its full text

- [x] 1.1 Make the CLI compile whole critical statements and refuse unlinked combined citations, with behavior regressions and migration guidance
  - Covers:
    - keel-task-capsule / A cited multi-line critical statement is wholly fingerprinted
    - keel-task-capsule / Critical identifiers in unresolved Covers entries fail visibly
    - keel-expectation-slice-evidence-gates / A critical statement's owned extent is structural
    - F1
    - F2
    - F3
    - D1
    - D2
    - D3
    - D4
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario whole-critical-statement-authority` drives public `keel gate task-start` and `task-complete` on anonymous fixtures: nested bullets and indented continuations change the fingerprint and cause recorded-anchor drift, while a peer bullet, same-level paragraph, and heading do not; colon-shaped openers still fail by name.
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario unlinked-critical-covers` drives public `keel gate task-start`: `D1、D2` and prose-wrapped citations fail by name; bare, ASCII-comma, annotated, and fact-with-resolved-question forms keep their established authority behavior.
    - M3 (regression): `npm test` passes the baseline and all registered scenarios, including existing critical-opener, annotation, question-scope, and drift gates.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9950f973d2a52be9ee6780071c64c3a143d35754ef37bbc2bb2e5e26448ff5cd
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario whole-critical-statement-authority` reports the scenario passing. Through public `task-start --json`, D1's authority text is `Preserve semantics. continuation alpha - nested detail alpha`; editing the continuation, the nested bullet, a bullet after a nested `#` line, or a lazy unindented continuation moves the fingerprint, while editing a peer bullet, an adjacent unbulleted `**D2** —` opener, a blank-separated paragraph, or the following heading does not. After `--record`, a nested-detail edit makes `task-complete` report `contract-drift`; `- D1: colon shape.` still fails with `Unparsed Covers critical statement: D1.` naming the `D1 —` shape.
    - M1.red: fail. With `src/core/task-contract.js` restored to HEAD (de4a5d8) and the scenario unchanged, it reported `whole-critical-statement-authority: the D1 authority omitted an owned line: 'Preserve semantics.'`. The later Review cases were each red against the first-pass implementation before it was corrected: `detail after a nested # edit left the cited contract fingerprint unchanged.` and `an adjacent unbulleted peer opener was absorbed into D1 authority.`
    - M1.green: pass. The same scenario passes against the working-tree compiler.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unlinked-critical-covers` reports the scenario passing. `D1、D2`, `D1，D2`, `D1 D2`, and `Implement both decisions（D1、D2）` each fail task-start with an `unresolved-covers` message naming the entry and `D1, D2`; `D1`, `D1, D2`, and `D1 — annotation` link `critical-statement` authority for exactly the cited references; `F13 (Q1 resolved: …)`, `D2: colon-form legacy description`, and `D2-compatible fixture text` keep passing.
    - M2.red: fail. With `src/core/task-contract.js` at HEAD (de4a5d8), it reported `unlinked-critical-covers: 'D1、D2' passed as unlinked prose.`
    - M2.green: pass. The same scenario passes against the working-tree compiler.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 192 scenarios, 1 skipped: output-survives-the-pipe.` The skip is this macOS host refusing `F_SETPIPE_SZ`, unrelated to this change; the existing critical-opener, widened-shape, unparsed-statement, annotation, question-scope, and drift scenarios all pass.
    - Review:
      - Status: pass
      - Acceptance check: Both scenarios drive the public `keel gate task-start` and `task-complete` commands on anonymous fixtures and assert the fingerprint value, the compiled authority text, and the refusal messages — the behavior the three Covers scenarios name — rather than the compiler's internals. Each owned-text shape moves the fingerprint and each peer boundary leaves it, which is E1; combined and prose-wrapped citations fail by name, which is E2; colon, annotation, and resolved-question forms keep their behavior, which is E3; the CHANGELOG states the `--record`/`--keep-evidence` reauthorization path and that old evidence is not trusted automatically, which is E4.
      - Scope check: The worktree diff against de4a5d8 touches only `src/core/task-contract.js`, `scripts/validate_plugin.py`, and `keel/CHANGELOG.md`, all in Touch, plus this change's own directory. The I1 wording `one-line statement` no longer appears outside this tasks.md. No colon syntax, question scope, or evidence-retention rule changed.
      - Findings: Resolved here: M1 — a `#` line nested inside a decision's detail cut ownership short, so a later sub-bullet escaped the fingerprint; a heading now ends the statement only when it is shallower than the item's content column. Resolved here: M1 — an unindented line continuing the opener's paragraph was left out, contrary to D1's boundary set; a lazy continuation is now owned unless it opens a block or another `D<n>`/`F<n>`/`A<n>`/`Q<n>` statement. Discard reason: the extent is still a structural line scan rather than a CommonMark parser — fenced code is owned by indentation only, and setext headings are not recognized — which design.md's Non-Goals and Risks accept; no reported case depends on either.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - A fix would require changing colon syntax, question citation scope, or accepting old evidence automatically.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - keel-expectation-slice-evidence-gates / An owned extent follows Markdown nesting
    - E1
    - E2
    - E3
    - E4
  - Read:
    - keel/CHANGELOG.md
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
    - openspec/specs/keel-task-capsule/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and promoted specs. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: the deltas are promoted, `node node_modules/.bin/openspec validate fingerprint-whole-critical-statements --strict` passes, and `npm test` reports no failing scenario, including `whole-critical-statement-authority`, which drives the nested-`#`, lazy-continuation, and adjacent-opener cases through public `task-start`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e1b33eb1c5cdf0afb3f66d1718a4b1a37d8b472535e6f06ce1f53b68e25089c8
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.80.0 to 5.81.0, the Unreleased #177 notes were folded into the 5.81.0 section, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes. The Stop Rule held: the bump touched only markers inside Touch.
    - M2: pass. Both deltas' ADDED requirements are promoted into `keel-task-capsule` and `keel-expectation-slice-evidence-gates`. `node node_modules/.bin/openspec validate fingerprint-whole-critical-statements --strict` (OpenSpec 1.13.2) reports the change valid, `openspec validate --specs --strict` reports `26 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 192 scenarios, 1 skipped: output-survives-the-pipe.`, with `whole-critical-statement-authority` passing its nested-`#`, lazy-continuation, and adjacent-opener cases.
    - Review:
      - Status: pass
      - Acceptance check: E1–E4 were proven by 1.1's M1–M3 through public `task-start`/`task-complete`; this task carries them into 5.81.0 with the requirements promoted where the next reader of each spec finds them. The added nesting requirement states the boundary 1.1's Review corrected, and M2's suite run exercises each of its scenarios through the public gate.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the two promoted specs — this task's Touch — plus 1.1's completed Touch files and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: 2.1 re-recorded once, from sha256:b8b15766c843f39cf9baa7feeb42f8ae11b61deeedc7d4bf2409d739cf5b7022, to cover the added requirement `An owned extent follows Markdown nesting` and name its cases in M2. No evidence existed under the earlier contract; M1 and M2 were both run after re-recording.

## Invalidates

- I1: "D2 — one-line statement" — `src/core/task-contract.js`'s unparsed-statement repair diagnostic implies the accepted statement itself must stay on one line. Updated by: 1.1

## Expectation Coverage

- E1: A cited multi-line critical statement, and only its owned text, moves the recorded contract when edited. Covered by: 1.1, 2.1
- E2: Unsupported combined or prose-wrapped critical citations do not pass as unlinked legacy authority. Covered by: 1.1, 2.1
- E3: Existing colon, annotation, and resolved-question supporting-detail boundaries remain explicit. Covered by: 1.1, 2.1
- E4: Existing anchors that move require explicit reauthorization, not silent evidence retention. Covered by: 1.1, 2.1
