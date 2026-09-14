# Tasks

## 1. The comparison and its reach

- [x] 1.1 `change-close` compares an `## Expectation Coverage` entry's cited `F<n>`/`D<n>`/`A<n>`/`Q<n>` identifiers against the `Covers:` of each task its `Covered by:` names, refusing a mismatch with the entry, the identifier, and where that identifier actually is covered; an entry citing none is untouched; and the close reports how many entries it compared and how many it did not, whenever the section declares any entry
  - Covers:
    - keel-expectation-slice-evidence-gates / A coverage claim is compared against the capsule it names
    - F1
    - F2
    - F3
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-coverage-claim-is-compared/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-coverage-claim-is-compared` scenario in `scripts/validate_plugin.py` drives `keel gate change-close` through the real CLI against fixtures built from issue #133's measured shapes, all four sharing one implementation and therefore one red. An entry citing `F2` and covered by a task whose `Covers:` omits it, while the change's other task names it, is refused with the entry, `F2`, and the task that does cover it. An entry citing an identifier no task covers is refused naming that fact and not naming a task as the place it is covered. An entry whose cited identifiers all appear in a named task's `Covers:` raises no problem, and runs first as the control. An entry citing nothing raises no problem, asserted against the mismatch fixture with its one citation removed. The `contradiction` fixture — one entry claiming an identifier is covered by a task whose `Covers:` omits it, and a second deferring the same identifier to a tracker URL — is refused by that same comparison with no rule about the two entries meeting, which is D3's claim that the declined suggestion is unnecessary. The report line carries both counts and is present when every entry was compared. Fails with: `Status: pass`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-reference-outlives-its-declaration` passes unchanged, so what a `Durable owner:` accepts is untouched by a change to what a `Covered by:` must agree with.
    - M3 (regression): the set of scenarios `npm test` reports as failing is identical to the set the same command reports on `origin/main`, so no scenario regressed. A differential rather than a pass, for the host reason owned by https://github.com/TanglmChris/keel/issues/137.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making a mismatch refusable requires an entry citing no identifier to be reported as deficient, because D4 records that 58% of the reporting repository's entries and 99% of this one's are prose and manufacturing a reference to satisfy a parser is the failure the rule exists to avoid.
    - Stop if the comparison needs to judge whether the named task's checks prove the expectation, because that is `keel-review-checklist`'s and a gate that claimed it would be asserting semantics with a parser.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4a335e453142508acbf0ad61b876c09846f68f6c0013c3605c06076b09ccd093
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-coverage-claim-is-compared` reports `a-coverage-claim-is-compared scenario passed.` Five fixtures, each a two-task change whose tasks cover `F1` and `F2` and whose design also declares `D1`, driven through `keel gate change-close --action archive`. `agree` closes with `Status: pass` and runs first, so every later refusal is attributable. `mismatch` (E1 cites `F2`, covered by 1.1) fails with `E1 says 1.1 covers F2, and task 1.1 does not name it in Covers. F2 is covered by task 2.1.` `orphan` (E1 cites `D1`) fails naming `D1` and `No task of this change covers D1.`, and is asserted not to contain `is covered by task`. `prose` — the `mismatch` entry with its one citation removed and nothing else changed — closes with `Status: pass`. `contradiction` (E1 claims `F2` covered by 1.1, E2 defers the same `F2` to a tracker URL) fails on `F2` through the comparison alone. The report reads `Expectation Coverage: compared 2 of 2 \`Covered by:\` entries against the Covers of the task named; 0 cited no expectation identifier and were not compared.`
    - M1.red: fail, for the right reason, with the declared signature. `a claim that task 1.1 covers F2 was accepted while 1.1's Covers names only F1; change-close returned Status: pass.` The control ran first and passed, so the red is the comparison being absent rather than the fixture failing to close.
    - M1.green: pass. Same command after `coversByIdentifier` and the comparison were added to `expectationProblems`.
    - M1.mutation: the two `orphan` assertions were added after the green, so neither had been red. Both were proven live by injection rather than left as assertions that never failed, per this repository's own precedent `an-assertion-that-never-failed-proves-nothing`: changing the no-task branch to name the claiming task instead reproduced `D1 is covered by task 1.1.` and the scenario failed with `the refusal points at a task as the place D1 is covered`. Reverted.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-reference-outlives-its-declaration` reports `a-reference-outlives-its-declaration scenario passed.` What a `Durable owner:` accepts — the unfilled-slot report, the undeclared-check refusal, the expanded v3 form — is untouched.
    - M3: pass. `npm test` reports `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved`, the identical set the same command reports at unmodified `origin/main`. No scenario regressed. Owned by https://github.com/TanglmChris/keel/issues/137.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a citing entry is compared and refused by name, that an entry citing nothing is untouched, and that the close reports its own reach. M1 proves each through `change-close` rather than by reading the function. Three shapes in it carry the weight. The `agree` control runs first, because a refusal asserted without it could be any of the dozen other things `change-close` refuses. The `prose` fixture is the `mismatch` fixture with one citation deleted, so "citing is optional" is proven against the case that would otherwise fail rather than against a fixture built to pass. And the `orphan` assertions are absence checks — the message must *not* name a task — which this repository's precedent says prove nothing until they have failed, so they were injected against rather than trusted.
      - Scope check: `git status --short` shows `src/core/gates.js` and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from the re-record.
      - Findings: one, fixed in this task. The first implementation attempt silently rewrote `invalidationProblems`'s `- None.` early return instead of `expectationProblems`'s, because the two functions share that line verbatim and the edit took the first match. It was not caught by the module loading — the file stayed valid JavaScript — and surfaced only as `invalidationProblems is not a function or its return value is not iterable` from a fixture that could not start. What found it was the fixture helper's own diagnostic, which had swallowed the CLI's stderr behind an unguarded `json.loads`; adding the guard turned an unreadable Python traceback into the actual cause in one run. The guard is now part of the scenario. Resolved here: M1
    - Blocker: none
    - Reauthorizations: M2 was folded into M1 and the two regression checks renumbered, before any Evidence was recorded, so nothing was invalidated. The original M2 asserted that the declined set-intersection rule is unnecessary because the comparison already refuses the contradiction it aimed at — a true claim with no red of its own, because it shares M1's one implementation. Two checks that cannot both have an honest red are one behavior split in half, which is the question `keel-review-checklist` asks at completion; asked here at authoring instead, because the answer was already visible.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E7 — the published spec and every version marker move with the behavior
  - Read:
    - keel/CHANGELOG.md
    - README.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The behavior was proven red-green in task 1.1, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `README.md` documents that citing identifiers is optional and that citing them is a claim the close compares, in the same place, so a reader cannot take the feature without its condition
    - M3: `keel/CHANGELOG.md` carries an entry giving issue #133's measured six, stating that the rule is a no-op on this repository's own archive and why that is recorded rather than hidden, and stating which of the report's two suggestions was declined and on what measurement
    - M4: the spec delta is promoted into `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`, `node node_modules/.bin/openspec validate a-coverage-claim-is-compared --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: the set of scenarios `npm test` reports as failing is identical to the set the same command reports on `origin/main`, for the host reason owned by https://github.com/TanglmChris/keel/issues/137
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:13eb24dcefc82d4e4032360d10752b0a96f48bbabcb7454692a522d9b087dda1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.59.0 to 5.60.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the three `keel:start` markers, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the version constants in `scripts/validate_plugin.py`.
    - M2: pass. `README.md` gains `## What a coverage claim is checked against` before `## Re-recording a contract`. It shows a citing entry, says what the close compares it against, and puts the condition in the same section rather than after it: citing is optional, an entry naming none is not refused and not reported as deficient, and the close reports how many entries it compared so a pass is not read as more than it is.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.60.0 - a coverage claim is compared`. It gives issue #133's measured six with the three shapes they fall into, states that the rule is a no-op on this repository's own archive — 347 of 351 entries cite nothing and the four that do arrived in 5.59.0 — and says the archive therefore cannot confirm the rule and the scenario carries the proof. It also states which of the report's two suggestions was declined and on what measurement: one hit in 83 archived changes, and that hit a false positive.
    - M4: pass. The delta is promoted — `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` carries `A coverage claim is compared against the capsule it names` with its five scenarios. `node node_modules/.bin/openspec validate a-coverage-claim-is-compared --strict` reports `Change 'a-coverage-claim-is-compared' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved` — the identical set the same command reports at unmodified `origin/main`. The release moved no scenario. Owned by https://github.com/TanglmChris/keel/issues/137.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than through the bump script's own report, so a marker neither knows about is what the Stop Rule is for; none appeared. M4 asserts the promotion through both tools that consume the published store, strict in both. M2 and M3 are the prose checks and share one job: this release adds a refusal, so the failure mode of its documentation is a reader who takes the check for more than it is. Both state the optional half beside the enforced half, and M3 additionally records the two things a changelog is usually allowed to omit — that the rule proves nothing against this repository's own history, and that one of the reporter's two suggestions was declined with the measurement that declined it.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `README.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted spec, and the twelve `.claude/`/`.codex/` marker files — plus `src/core/gates.js` and task 1.1's scenario, already declared complete by 1.1 and untouched here, plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: none beyond the one task 1.1 resolved and the host defect M5 inherits. Durable owner: https://github.com/TanglmChris/keel/issues/137
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel gate change-close` … validate contract/evidence shape only" as a reader would
  apply it to `## Expectation Coverage` — the section had one closure form whose content
  was never read, and after this release the citing entries are compared. The sentence in
  `AGENTS.md` stays literally true, because comparing two declared identifier lists is
  still shape rather than semantics.
  Discard reason: the wording is correct and this change does not make the gate semantic.
  What the comparison reads is two lists the author already declared, and whether the
  named task's checks actually prove the expectation is untouched and still
  `keel-review-checklist`'s. Rewording it to suggest the gate now judges coverage would be
  exactly wrong.

## Expectation Coverage

- E1: An entry citing identifiers and naming a task is refused when that task's `Covers:` omits one, and the refusal names the entry, the identifier, and where it actually is (F1, F2, D1, D2). Covered by: 1.1
- E2: An entry citing no identifier is neither refused nor reported as deficient (D4). Covered by: 1.1
- E3: The close reports how many entries it compared and how many it did not, including when it compared all of them (D5). Covered by: 1.1
- E4: The report's set-intersection suggestion is not implemented, and the contradiction case it aimed at is refused by the comparison instead (D3, D6). Covered by: 1.1
- E5: The rule is a no-op on this repository's own archive, so the scenario rather than the archive carries the proof (F3). Covered by: 1.1
- E6: Whether an identifier cited inside an entry is always a claim rather than an incidental mention. Measured at 0 false positives over 534 entries, which is evidence and not a construction — the rule declined in D3 failed on exactly this distinction. Cites no `A<n>` on purpose, so that nothing sits on the covered and the deferred side at once. Durable owner: https://github.com/TanglmChris/keel/issues/133
- E7: The published spec and every version marker move with the behavior. Covered by: 2.1
