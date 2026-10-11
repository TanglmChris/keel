# Tasks

## 1. Marker words in capitals

- [x] 1.1 The concreteness test matches marker words only in capitals
  - Covers:
    - keel-task-capsule / Marker words read as unfilled only in capitals / A lowercase marker word is prose
    - keel-task-capsule / Marker words read as unfilled only in capitals / A capitalised marker word is still a slot
    - keel-task-capsule / Marker words read as unfilled only in capitals / An angle-bracket slot is still a slot
    - keel-core-gates / A rejection becomes a Reauthorizations entry the author writes, not a gate write / An unfilled slot is refused
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/task-contract.js
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario marker-words-in-capitals` runs the real `task-start` over a check naming `each todo and its placeholder text` in plain words and requires it to pass, runs `task-start` then `task-complete` over Evidence reading `With --ack on post and todo` in plain words and requires no unfilled-slot problem, and runs `task-start` over checks carrying a bare `TODO`, a bare `PLACEHOLDER`, and a bare `<value>` and requires each to fail with `non-concrete-verify` naming that token. Fails with: `marker-words-in-capitals:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario inline-code-is-concrete` and `--scenario non-concrete-verify-diagnostic` still pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:39230a7e1889dcdbf11d36c71a03801b2f298c2152a640ef7ba2efdeb1f21d7c
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario marker-words-in-capitals` reports `marker-words-in-capitals scenario passed.`
    - M1.red: fail. Before the change the scenario reported `marker-words-in-capitals: a check naming a todo and a placeholder in lowercase prose was judged unfilled.`, carrying the declared signature `marker-words-in-capitals:`; the gate's message was `M1 carries the unfilled slot` naming the lowercase word.
    - M1.green: pass. With `UNFILLED_TOKEN` matching `TODO`, `TBD`, and `PLACEHOLDER` case-sensitively, the scenario passes all five shapes: lowercase prose in a check and in Evidence is concrete, and bare `TODO`, `PLACEHOLDER`, and `<value>` are each reported as `non-concrete-verify` naming the token.
    - M2: pass. `inline-code-is-concrete` and `non-concrete-verify-diagnostic` each report `scenario passed.`
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 243 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real `task-start` and `task-complete` over the issue's own Evidence wording and over each form that must still be refused, and checks the named token, not only the verdict.
      - Scope check: `git status --short` lists `src/core/task-contract.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a marker written in lowercase as a genuine slot, such as a bare `todo` left in a Touch entry, is no longer caught by this test; D1 accepts that, because capitals are the form people use to mark something unfinished and the Touch path check still refuses a path that does not exist.
    - Blocker: none
    - Reauthorizations: the first `task-start` refused this task's own M1 for the defect it fixes, naming the lowercase `todo` in the quoted Evidence wording. The quoted wording was fenced in inline code before the anchor was recorded, and left fenced so the fingerprint does not move.

## 2. Release

- [x] 2.1 Release and promote the specs
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
    - openspec/specs/keel-core-gates/spec.md
    - openspec/specs/keel-task-capsule/spec.md
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
    - M1: `node scripts/bump_version.js patch` moves every marker to the next patch version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED and MODIFIED requirements are promoted into `openspec/specs/keel-task-capsule/spec.md` and `openspec/specs/keel-core-gates/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:78a71e020ff47510ee4a9db987ab3f58f7e47c07acc09a5a35e6e06cfc6b0182
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.102.1. With the 5.102.1 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement follows the required-field token requirement in `keel-task-capsule`, and the MODIFIED Reauthorizations requirement replaces its published copy in `keel-core-gates`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published specs state the token set with its case, and the changelog names the issue and the rule.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the two specs, all in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.102.1 reports `validation --all passed: baseline plus 243 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "Angle brackets, TODO, TBD, and the word placeholder all read as unfilled, including inside prose." — the `non-concrete-verify` message in `src/core/task-contract.js`. Updated by: 1.1
- I2: "carrying no unfilled `<slot>`/`TODO`/`TBD`/`placeholder` token" — the Reauthorizations requirement in `openspec/specs/keel-core-gates/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: Ordinary lowercase prose naming a todo or a placeholder is concrete, while capitalised markers and angle-bracket slots are still refused (D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
