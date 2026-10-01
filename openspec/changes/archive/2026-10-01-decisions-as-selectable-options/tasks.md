# Tasks

## 1. Decisions are offered as choices

- [x] 1.1 The resident protocol and the alignment skill direct enumerable decisions through the host's structured-choice surface
  - Covers:
    - keel-expectation-alignment / Enumerable decisions are offered as selectable options
    - F1
    - D1
    - D2
    - D3
  - Touch:
    - AGENTS.md
    - src/skills/keel-align-expectations/SKILL.md
    - plugins/keel/skills/keel-align-expectations/SKILL.md
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario decisions-are-selectable` requires the managed block of `AGENTS.md` under `## User-facing communication`, and the Deep path of `keel-align-expectations` in both `src/skills` and `plugins/keel/skills`, to state that an enumerable decision is asked through the host's structured-choice surface with the recommendation first, that prose remains for open questions and hosts without one, and that the skill names no host tool such as `AskUserQuestion`. Fails with: `does not offer decisions as selectable options`
    - M2 (regression): `npm test` passes the baseline and all registered scenarios, including the skill source/shipped-copy equality and resident-block checks.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b301a55b1950b5b7717c2c068a963bb7a20cc1d49dfa013516cab7f8764bfc2d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario decisions-are-selectable` reports the scenario passing: `AGENTS.md`'s managed `## User-facing communication` and the `## Deep path` of `keel-align-expectations` in `src/skills` and `plugins/keel/skills` each state that an enumerable decision goes through the host's structured-choice surface, recommended option first and marked, with prose kept for open questions and hosts without one; neither skill copy names `AskUserQuestion`.
    - M1.red: fail, for the declared reason. Before the wording changed, the scenario reported `decisions-are-selectable: AGENTS.md User-facing communication does not offer decisions as selectable options.`, carrying the declared signature `does not offer decisions as selectable options`.
    - M1.green: pass. The same scenario passes after the three files gained the rule.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 193 scenarios, 1 skipped: output-survives-the-pipe.` (macOS `F_SETPIPE_SZ`, unrelated). The source and shipped skill copies are byte-identical.
    - Review:
      - Status: pass
      - Acceptance check: The requirement's two scenarios are about what a reader of the protocol and the skill is told; M1 reads exactly those sections in all three carriers and requires each element of the rule — the surface, the recommendation first, and the prose fallback for open questions and surface-less hosts — and the absence of a host tool name, which is D2. Whether an agent actually uses the surface is presentation and stays out of any gate, which is D3.
      - Scope check: The diff touches `AGENTS.md`, both `keel-align-expectations/SKILL.md` copies, `scripts/validate_plugin.py`, and `keel/CHANGELOG.md`, all in Touch, plus this change's own directory. The I1 wording `host runtime's concern` no longer appears in either skill copy.
      - Findings: Discard reason: the `/opsx:propose` overlay in `bin/keel.js` (and the generated propose command and skills) still summarizes the deep path as "ask one material decision at a time … provide a recommended answer". It does not contradict the new rule and directs the agent to run `keel-align-expectations`, which carries it; changing the overlay would regenerate seven files for no change in behavior.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - Stating the rule would require naming a host tool in portable skill text, or adding a gate that judges presentation.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
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
    - openspec/specs/keel-expectation-alignment/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and a promoted spec. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: the deltas are promoted, `node node_modules/.bin/openspec validate decisions-as-selectable-options --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5941baac189430f49a2676ecb348d5f58d9d83ac9f95319b84403075f22acf30
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.81.0 to 5.82.0, the Unreleased #174 notes were folded into the 5.82.0 section, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes. The Stop Rule held.
    - M2: pass. The ADDED requirement is promoted into `keel-expectation-alignment`. `node node_modules/.bin/openspec validate decisions-as-selectable-options --strict` (OpenSpec 1.13.2) reports the change valid, `openspec validate --specs --strict` reports `26 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 193 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: E1 was proven by 1.1's M1 against all three carriers; this task carries it into 5.82.0 with the requirement promoted where the next reader of the alignment spec finds it.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the promoted spec — this task's Touch — plus 1.1's completed Touch files and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "how questions are presented interactively is the host runtime's concern" — `keel-align-expectations` Purpose, in `src/skills` and `plugins/keel/skills`, which reads as permission to ask enumerable decisions in prose. Updated by: 1.1

## Expectation Coverage

- E1: On a host with a structured-choice surface, Keel's resident protocol and alignment skill direct the agent to offer an enumerable decision as selectable options with the recommendation first, while open questions and hosts without the surface keep prose. Covered by: 1.1, 2.1
