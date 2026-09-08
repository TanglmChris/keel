# Tasks

## 1. What a re-record leaves standing

- [x] 1.1 `keel gate task-start --record --keep-evidence M1,M3` narrows the stale-evidence report to the checks not declared, naming the declared ones and attributing the narrowing to the declaration, refusing a label the contract does not declare and refusing the flag without `--record`, while completion is unchanged
  - Covers:
    - keel-core-gates / A re-record may carry what the author declares survived it
    - D2
    - D3
    - D4
    - D5
    - D6
    - A1
    - F1
    - F2
  - Read:
    - bin/keel.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/evidence-survives-what-did-not-change/design.md
  - Touch:
    - bin/keel.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `evidence-survives-what-did-not-change` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI against a fixture whose recorded anchor differs from the compiled one. With `--record` alone the report names all three checks as stale, which is the control. With `--record --keep-evidence M1,M3` it names only `M2` as stale and names `M1, M3` as declared unaffected, attributing that to the declaration. `--keep-evidence M9` is refused naming `M9`. `--keep-evidence M1` without `--record` is refused. The task then completes exactly as it would have: `task-complete` still refuses it with Evidence missing for any label, and still refuses a red-green strategy with no `.red`/`.green`, asserted by running both.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario anchor-reverification-bound` passes unchanged, so when a re-record is reported as landing a different contract is untouched.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if narrowing the report requires excluding any field from the fingerprint, because D1 records that the tag the reporter names is the one that changes an evidence obligation and excluding it would reopen the escape hatch 5.50.0 closed.
    - Stop if the declaration changes anything `task-complete` requires, because it is a statement about the past and completion is about the present.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2c9bfe5e56b688522677893dad7dc55e5d035f05d84d7c2748edab44cc6aa8f2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario evidence-survives-what-did-not-change` reports `evidence-survives-what-did-not-change scenario passed.` Against a three-check fixture whose recorded anchor differs from the compiled one: `--record` alone reports the blanket sentence, which is the control; `--record --keep-evidence M1,M3` reports `Evidence for M2 is stale; clear or re-verify it before completing this task. M1, M3 were declared unaffected by this contract change — a declaration Keel records and does not verify, since it retains only the previous fingerprint and cannot compare a check's former text to its current one. State the reason in Reauthorizations.` `--keep-evidence M9` is refused naming `M9` and listing what the contract does declare. `--keep-evidence M1` without `--record` is refused. Completion is asserted unchanged by running it: a `vertical-tdd` task that declared all three kept still fails `task-complete` with `missing-strategy-evidence`.
    - M1.red: fail, for the right reason. Before the flag existed the scenario reported `a declaration refused a valid re-record; ''` — the CLI rejected the unknown option before any gate ran, which is the state where an author has no way to say what they can plainly see.
    - M1.green: pass. Same command after `--keep-evidence` was parsed, validated against the compiled contract, and used to narrow the report.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario anchor-reverification-bound` reports `anchor-reverification-bound scenario passed.` When a re-record is reported as landing a different contract is untouched; only what that report says changed.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 167 scenarios.` — up from 166 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the report narrows to what is still stale, names what was declared and by whose authority, refuses an unknown label and a declaration without a re-record, and changes nothing about completion. M1 proves all five. The control run matters most: a scenario asserting only "M2 appears" would pass against an implementation that never mentioned the others either. The completion half is proven by running `task-complete` rather than by reading the code, because the risk being checked is that a flag about the past quietly reaches the present.
      - Scope check: `git status --short` shows exactly this task's three Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, fixed in this task. `assertion-shape-count` refused the scenario: its unknown-label check guarded two distinct failures — the declaration was not refused at all, and the refusal did not name the label — behind one message, so whichever fired the reader would have been told both. The bound is 80 OR-guarded sites and this was the 81st. Split into two assertions with their own messages rather than raising the bound, which is the third time this session that check has caught a condition worth splitting. Resolved here: M3
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a declared check is not reported stale, and the narrowing is attributed
    - E2 — an unknown label and a declaration without a re-record are both refused
    - E3 — completion is unchanged
    - I1 — the published wording this change makes stale
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - README.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-core-gates/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The behavior was proven red-green in task 1.1, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `README.md` documents the flag, what it narrows, and states in the same place that Keel does not verify the declaration and why
    - M3: `keel/CHANGELOG.md` carries an entry giving the measured cost from issue #112, stating that the fingerprint stays whole and why the reporter's own example is the wrong thing to exclude from it, and stating what the flag does not verify
    - M4: the spec delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node node_modules/.bin/openspec validate evidence-survives-what-did-not-change --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:eb868754a6e5b630c7a11f9c177793a1f9062a0911a6a7003d595dbfe57a0d9a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.54.0 to 5.55.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `README.md` gains a `## Re-recording a contract` section before `## Pausing a change`. It shows the flag, states what the report narrows to, and puts the limit in the same paragraph as the feature: Keel does not verify the claim, because it keeps only the previous fingerprint and not the capsule behind it, so the reason belongs in `Reauthorizations` where a reviewer can disagree with it.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.55.0 - evidence survives what did not change`. It gives the measured cost from issue #112 — four re-verifications, the experiment timings, the testbench that had to be broken and restored — states that the fingerprint stays whole and that the reporter's own `(regression)` example is precisely the wrong thing to exclude from it, and states what the flag does not verify.
    - M4: pass. The delta is promoted — `openspec/specs/keel-core-gates/spec.md` carries `A re-record may carry what the author declares survived it` with its four scenarios. `node node_modules/.bin/openspec validate evidence-survives-what-did-not-change --strict` reports `Change 'evidence-survives-what-did-not-change' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 167 scenarios.` — the same count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M4 asserts the promotion through both tools that consume the published store. M2 and M3 are the prose checks, and both have the same job: this is a flag that relaxes a warning, so the failure mode of the documentation is a reader who takes it for a verification. Both put the limit beside the feature rather than in a footnote, and M3 additionally records why the obvious alternative — excluding tags from the fingerprint — is the one thing not to do.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `README.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-core-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files — plus `bin/keel.js` and `src/core/gates.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Execution evidence produced under the previous contract is stale; clear or re-verify it" — the
  re-record warning in `src/core/gates.js` and the scenarios asserting it. It says every check, which
  is what an author acting on it in good faith re-runs, and after this release it says which.
  Updated by: 1.1
- I2: "The gate cannot judge which Evidence survives" — the comment above that warning. It stays true
  and is the reason the flag exists rather than an automatic rule.
  Discard reason: the sentence is correct and this change does not make the gate judge. What changes
  is that the author may now say what they judged, in a form the gate records and the Review can
  challenge; rewording the comment to suggest the gate now knows would be exactly wrong.

## Expectation Coverage

- E1: A declared check is not reported stale, and the report names both what remains stale and what was declared, attributing the narrowing. Covered by: 1.1, 2.1
- E2: A label the contract does not declare is refused, and the flag without `--record` is refused. Covered by: 1.1, 2.1
- E3: Every completion requirement is unchanged — per-label Evidence, red-green, and the semantic Review. Covered by: 1.1
- E4: Verifying that a declaration is true. Discard reason: D3 records that the gate retains only the previous fingerprint and cannot compare a check's former text to its current one, which is the same limit https://github.com/TanglmChris/keel/issues/115 owns; the claim belongs to the Reauthorizations note the protocol already requires.
