# Tasks

## 1. Classify the suite's evidence and carry it into each release

- [x] 1.1 Classify scenarios by evidence kind, print it after a passing run and in release notes, and settle the desktop and Codex rows
  - Covers:
    - keel-validation-runner / The suite states what kind of evidence ran / A scenario that reaches a stand-in through a helper, a hook payload or a script is counted as one
    - keel-validation-runner / The suite states what kind of evidence ran / A passing run states its evidence
    - keel-validation-runner / Each release's notes carry its evidence / A release's notes carry the evidence section
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
  - Read:
    - openspec/changes/release-evidence/design.md
    - scripts/validate_plugin.py
    - scripts/validation/common.py
    - .github/workflows/publish.yml
  - Touch:
    - scripts/validation/evidence.py
    - scripts/validate_plugin.py
    - scripts/validation/selfcheck.py
    - scripts/validation/registry.py
    - .github/workflows/publish.yml
    - docs/host-contract.md
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario release-evidence-classes`: `--evidence` lists `shift-cli-self-shift`, `chat-claude-hooks`, `codex-receiving` and `update-pack-install` as stand-in host and `version-alignment` as deterministic, with counts adding up to the registry's size and derived markers including `KEEL_CLAUDE` and `CLAUDE_CODE_SESSION_ID`; `--evidence --markdown` prints `## Evidence` with both counts, the `measured` row count of `docs/host-contract.md` and the scenarios that can skip; the publish release step appends that output to `notes.md`; and `--group docs` ends with an `evidence:` line whose counts add up to its verified count and that names `docs/host-contract.md`. Fails with: `release-evidence-classes:`
    - M2 (regression): the baseline, `--group selfcheck`, `--scenario release-notes-name-the-directory-branch`, `--scenario publish-awaits-registry` and `--scenario assertion-shape-count` pass, and every scenario `docs/host-contract.md` cites is still registered.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ee00abfd0c709d725dc066b11c38dafdef286c9d96445d7c2ca1d81dcfceb9ce (keel 5.185.0)
    - M1: pass. Result: `release-evidence-classes scenario passed: 181 deterministic, 136 stand-in host.`
      - `--evidence` classes `shift-cli-self-shift` (`KEEL_CLAUDE`), `chat-claude-hooks` (hook payload only), `codex-receiving` (through `scripts/validate_codex_receiving.py` only) and `update-pack-install` (a fake `npm` on PATH) as stand-in host, and `version-alignment` as deterministic. The two classes are disjoint and cover all 317 registered scenarios.
      - The derived markers include `KEEL_CLAUDE` and `CLAUDE_CODE_SESSION_ID`.
      - `--markdown` prints `## Evidence` with 181 and 136 scenarios, `6 conditions` measured (counted independently from `docs/host-contract.md`), and the five scenarios that can skip.
      - The publish release step appends `validate_plugin.py --evidence --markdown >> notes.md`.
      - `--group docs` ends `evidence: 22 deterministic, 0 against a stand-in host, none on a real host (host measurements: docs/host-contract.md)`, after `validation --group docs passed: 22 scenarios.`
    - M1.red: `release-evidence-classes: the markers derived from Keel's sources do not include KEEL_CLAUDE: []`. This was before `scripts/validation/evidence.py` existed: `--evidence` fell through to the baseline, and its output carried no classification.
    - M1.green: `release-evidence-classes scenario passed: 181 deterministic, 136 stand-in host.` These are now in place:
      - `scripts/validation/evidence.py` derives the markers, classifies scenarios through an AST reachability closure plus the scripts the closure names, and renders both forms.
      - `validate_plugin.py` gains `--evidence [--markdown]`, and `run_all` and `run_group` print the evidence line after a pass.
      - `publish.yml` appends the section.
      - `docs/host-contract.md` and both READMEs describe it.
    - M2: pass.
      - The baseline exits 0 (`Keel v4.1.0 baseline validation passed.`). Its standard-library import check now also reads `evidence.py`.
      - `--group selfcheck` reports `validation --group selfcheck passed: 9 scenarios, 1 skipped: output-survives-the-pipe.` followed by its evidence line.
      - `release-notes-name-the-directory-branch`, `publish-awaits-registry` and `assertion-shape-count` (74 sites) pass.
      - All 10 scenario names `docs/host-contract.md` cites are still registered.
    - Review:
      - Status: pass
      - Acceptance check:
        - M1 drives the public entry points (`--evidence`, `--evidence --markdown`, `--group docs`) and the shipped workflow text. It covers each path by which a scenario reaches a stand-in: an override variable, a helper, a hook payload, a delegated script, and a program on PATH.
        - The measured count is computed independently of the code under test.
        - D6 is the rewritten "Outside this contract" section.
      - Scope check: the changed files are the eight in Touch (one new: `scripts/validation/evidence.py`) plus this change's record. `src/` and `bin/` are unchanged.
      - Findings:
        - `runner-skip-accounting` drives `run_all` over a synthetic registry whose functions are `None`, and the first classifier crashed on it. A scenario whose code cannot be read is now counted as stand-in host, the side that claims less. Resolved here: M2
        - `release-evidence-classes` names `KEEL_CLAUDE` and `CLAUDE_CODE_SESSION_ID` in its own assertions, so it counts itself as stand-in host. Discard reason: the design accepts this over-approximation (D2), which errs toward claiming less real evidence. Rewriting the marker names to dodge the scan would hide that the classifier is textual.
        - Whether a timed-out `claude --bg` had started its session stays unverified. Durable owner: https://github.com/TanglmChris/keel/issues/408
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
    - openspec/specs/keel-validation-runner/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-validation-runner`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes and ends with an `evidence:` line.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0b8b8fa02c2de0fdb73b846373628b0beb39c32e397dfa6b97477aa8b2413796 (keel 5.185.0)
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.186.0, and the changelog section "5.186.0 - The suite and each release say what kind of evidence ran" replaced the `TODO` stub, keeping its Version alignment line. Result: `version-alignment scenario passed.`
    - M2: pass. The two ADDED requirements were promoted into `openspec/specs/keel-validation-runner/spec.md`. Result: `published-specs-validate-strictly scenario passed: 33 published specs validate strictly against openspec 1.14.0.`
    - M3: pass. `npm test` ran on commit 6721fa0e with a clean tree, starting 13:27:44 at load 7, and exited with rc=0. It printed `validation --all passed: baseline plus 316 scenarios, 1 skipped: output-survives-the-pipe.` and then `evidence: 180 deterministic, 136 against a stand-in host, none on a real host (host measurements: docs/host-contract.md)`. 180 + 136 = 316, the verified count. The skipped scenario is a deterministic one.
    - Review:
      - Status: pass
      - Acceptance check:
        - M1 and M2 run the marker and published-spec scenarios on the written release.
        - M3 is the whole suite on the release commit, and it ends with the new evidence line, whose counts add up to the verified count.
      - Scope check: the bump touched only listed Touch files, plus this change's record.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: In `docs/host-contract.md`, the "Not covered by this loop" list says "the Claude desktop app path …" and "Codex" are unverified. Updated by: 1.1.
- I2: The `npm test` comment in `README.md` reads "one validate_plugin.py --all run: baseline + all scenarios in parallel", and its counterpart in `README.zh-CN.md` reads "一次 validate_plugin.py --all：baseline + 全部场景并行". Neither mentions the evidence line. Updated by: 1.1.

## Expectation Coverage

- E1: Each passing run, and each release's notes, state how many scenarios were deterministic and how many ran against a stand-in host, that none ran on a real host, where real-host measurements are, and which scenarios can skip (#408; D1–D7). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Follow-ups

- Whether a timed-out `claude --bg` had started its session stays unverified in `docs/host-contract.md`. Durable owner: https://github.com/TanglmChris/keel/issues/408
