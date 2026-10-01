# Tasks

## 1. Derive the bookkeeping, keep the judgment

- [x] 1.1 `task-start --record` fills a valid task's missing record slots from its capsule
  - Covers:
    - keel-core-gates / Gate results expose capsule and fingerprint evidence
    - F1
    - D1
    - D2
  - Touch:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario record-derives-skeleton` drives public `keel gate task-start --record` on anonymous fixtures: a `vertical-tdd` task with `M1`, `M2 (regression)`, and `M3` declaring `Detects:` and no Evidence gains exactly `Contract` (recorded), `M1`, `M1.red`, `M1.green`, `M2`, `M3`, `M3.red`, `M3.green`, `M3.detects`, a pending Review with four fields, `Blocker: none`, and `Reauthorizations: none`, with no other line changed; a second run is byte-identical; a concrete `M1` result is kept verbatim while only missing slots are added; an `evidence-first` task gains no `.red`/`.green`; a task with no `Strategy:` is refused and nothing is written, guard manifest included; `task-complete` still refuses the filled task as unfilled; without `--record` the `evidence-label-mismatch` message names `--record`. Fails with: `record-derives-skeleton:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` passes with its missing-anchor case updated to the filling behavior and every other record, re-record, and unchanged case as before.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:67cefb37a6a5ef1e107dd85e8c3a714508d25d9ed2b8c768e6ad9ff9db6995d7
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario record-derives-skeleton` reports the scenario passing. On a `vertical-tdd` task with `M1`, `M2 (regression)`, and `M3` declaring `Detects:` and no Evidence, `--record` reports `recorded` and adds exactly the Evidence header, the recorded Contract line, `M1`, `M1.red`, `M1.green`, `M2`, `M3`, `M3.red`, `M3.green`, `M3.detects`, a pending Review with four fields, `Blocker: none`, and `Reauthorizations: none`, removing no line; a second run reports `unchanged` and is byte-identical; `task-complete` still refuses the filled task; a concrete `M1: pass. …` line is kept verbatim and only the missing slots join it; an `evidence-first` task gains no `.red`/`.green`; a task with no `Strategy:` is refused with `tasks.md` and the guard manifest untouched; without `--record`, the `evidence-label-mismatch` message names `--record`.
    - M1.red: fail. Before the gate change, the scenario reported `record-derives-skeleton: --record refused a valid task with no Evidence: [{'code': 'missing-field', 'message': 'Evidence must be concrete.'}, {'code': 'evidence-label-mismatch', …}]`, carrying the declared signature `record-derives-skeleton:`.
    - M1.green: pass. The same scenario passes against the working tree.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` reports the scenario passing. Its record fixture now carries the complete slot set the template writes, so the record, re-record, and unchanged cases still assert that only the Contract line changes; its missing-anchor case now expects the anchor to be added and the gate to pass.
    - Review:
      - Status: pass
      - Acceptance check: M1 drives only the public `task-start --record` and `task-complete` commands and asserts the bytes written, which is what the modified requirement specifies: which slots, in which form, nothing rewritten, idempotence, refusal with no write on an authoring error, and that completion still refuses placeholders. M2 keeps the earlier record behavior honest for tasks whose slots are already complete. A full `npm test` at this point failed only on `review-checklist-defers-to-gate` being unregistered, which is 1.2's scenario.
      - Scope check: The diff touches `src/core/gates.js` (slot derivation, the `taskStart` wrapper, and the I1 message), `src/core/task-contract.js` (the `--record` hint on `evidence-label-mismatch`), `scripts/validate_plugin.py` (the new scenario and the core-gates fixture and case), and nothing else in Touch yet; `keel/CHANGELOG.md` is written in 2.1's release notes via 1.2's Unreleased entry. Covers, Touch, Verify, and Acceptance of a filled task are never written.
      - Findings: Discard reason: a `Review:` line that exists with some of its four fields missing is left as is, because only an absent Review block is derived; the four fields are a fixed template whose partial presence means an author edited it, and task-complete names the missing field.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - Filling would require writing a result, a Review verdict, or a keep reason, or touching Covers, Touch, Verify, or Acceptance.

- [x] 1.2 The review checklist stops restating what task-complete refuses on its own
  - Covers:
    - keel-expectation-slice-evidence-gates / The review checklist does not restate mechanical refusals
    - F3
    - D3
  - Touch:
    - src/skills/keel-review-checklist/SKILL.md
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario review-checklist-defers-to-gate` requires both copies of `keel-review-checklist/SKILL.md` to omit instructions to confirm the Contract line's fingerprint or the presence of `.red`/`.green` Evidence, and to keep that evidence-first tasks name their observable proof and that behavioral checks prove Acceptance through the public interface. Fails with: `review-checklist-defers-to-gate:`
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:419930dac58ce9facfe3f0cca9d6830664b65fb79adf2ae28a41297e2dd1457c
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario review-checklist-defers-to-gate` reports the scenario passing: neither copy of `keel-review-checklist/SKILL.md` asks the agent to confirm the Contract line's fingerprint or the existence of `.red`/`.green` Evidence, and both keep `evidence-first tasks`, `observable proof`, `through the public interface`, and `not build-only or shape-only`. The two copies are byte-identical.
    - M1.red: fail. Before the edit, the scenario reported `review-checklist-defers-to-gate: src/skills keel-review-checklist still restates a gate refusal: 'Evidence \`Contract\` line records the task-start capsule fingerprint'`, carrying the declared signature `review-checklist-defers-to-gate:`.
    - M1.green: pass. The same scenario passes after the two bullets were replaced by one sentence naming what `task-complete` already refuses and what it cannot judge.
    - Review:
      - Status: pass
      - Acceptance check: The requirement concerns what the checklist tells its reader; M1 reads both shipped copies and asserts both the absence of the restatements and the presence of the judgments the gate cannot make, so a deletion that took a criterion with it would fail. The gate-side refusals the removed text restated are `missing-contract-anchor`/`contract-drift` and `missing-strategy-evidence` in `src/core/gates.js` (F3).
      - Scope check: The diff touches both `keel-review-checklist/SKILL.md` copies, `scripts/validate_plugin.py`, and `keel/CHANGELOG.md`, all in Touch, plus this change's own directory. `npm test` reports `validation --all passed: baseline plus 197 scenarios, 1 skipped: output-survives-the-pipe.`
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - A removed sentence turns out to carry a criterion no gate enforces.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
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
    - openspec/specs/keel-core-gates/spec.md
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
    - M2: the deltas are promoted, `node node_modules/.bin/openspec validate record-derives-its-skeleton --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:131ff4bce0973d35c4867e15c281a28cc25266d09da4d74ed076814c22e78b61
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.83.0 to 5.84.0, the Unreleased #179 notes were folded into the 5.84.0 section, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes. The Stop Rule held.
    - M2: pass. The modified requirement replaces its predecessor in `keel-core-gates` (the I3 wording is gone) and the added requirement joins `keel-expectation-slice-evidence-gates`. `node node_modules/.bin/openspec validate record-derives-its-skeleton --strict` (OpenSpec 1.13.2) reports the change valid, `openspec validate --specs --strict` reports `27 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 197 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: E1 and E2 were proven by 1.1 and 1.2; this task carries them into 5.84.0 with both requirements where the next reader of each spec finds them. Its own record slots, like 1.2's, were written by the 1.1 behavior: `task-start --record` reported `filled: M1, M2, Review, Blocker, Reauthorizations`.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the two specs — this task's Touch — plus 1.1 and 1.2's completed files and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario after all tasks, including `record-derives-skeleton`, `review-checklist-defers-to-gate`, `core-gates`, and the skill-document checks.

## Change Evidence

- C1: pass. After 2.1's bump and spec promotion, `npm test` reports `validation --all passed: baseline plus 197 scenarios, 1 skipped: output-survives-the-pipe.` (macOS `F_SETPIPE_SZ`, unrelated), including `record-derives-skeleton`, `review-checklist-defers-to-gate`, and `core-gates`.

## Invalidates

- I1: "Add \"- Contract: pending\" to its Evidence." — the `record-refused` message in `src/core/gates.js`, which `--record` no longer needs. Updated by: 1.1
- I2: "confirm concrete per-label `.red` and `.green` Evidence exists for the same check" — `keel-review-checklist` Deterministic gate check, both copies. Updated by: 1.2
- I3: "MUST refuse deterministically — writing nothing — only when the selected task has no `- Contract:` line at all" — `openspec/specs/keel-core-gates/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A valid task needs no hand-written record slots before `--record`; derived slots read `pending`, nothing written is a result or verdict, and authoring errors still refuse with no write. Covered by: 1.1, 2.1
- E2: Review guidance keeps every judgment the gate cannot make and no longer restates what `task-complete` refuses mechanically. Covered by: 1.2, 2.1
