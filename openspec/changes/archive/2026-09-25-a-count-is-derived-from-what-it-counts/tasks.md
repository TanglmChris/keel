# Tasks

## 1. The check asks the module

- [x] 1.1 `src/core/config.js` exports the declaration names it reads, and the header assertion is derived from that export — naming the declaration missing from the header instead of comparing counts
  - Covers:
    - keel-validation-runner / An assertion about a set is derived from that set / A document missing a member fails, naming it
    - keel-validation-runner / An assertion about a set is derived from that set / Adding a member costs only the document
    - F1
    - F2
    - D1
    - D2
    - D3
    - A1
  - Read:
    - src/core/config.js
    - scripts/validate_plugin.py
    - openspec/changes/a-count-is-derived-from-what-it-counts/design.md
  - Touch:
    - src/core/config.js
    - scripts/validate_plugin.py
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-count-is-derived-from-what-it-counts` scenario reads the exported declaration list by running `node` against `src/core/config.js`, asserts it holds all six names this repository reads, and asserts that `keel/config.yaml`'s header names every one of them. It then plants a seventh name into a copy of the export and asserts the check fails **naming that name** and reporting no count — the derivation proved by feeding it a member the header cannot contain. Fails with: `the assertion is a literal`
    - M2: the English numeral is gone from the assertion. A copy of `keel/config.yaml` whose header names all six declarations while miscounting them in prose passes, because membership is the checkable property and a count is a lossy restatement of it. Fails with: `still says six declarations`
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario delegation-resident-text` passes, and every `continuation` and delegation clause it pins is untouched — the count assertion is replaced inside it, not the scenario's subject.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the declaration list has to be read by regexing `src/core/config.js`, because D1 records that a regex over the source is a second copy of the same literal one level down.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:48e1d8e7aa3b5015e5e36cbce881a35926bd5c0c642036579c6d4ff7f3a7322b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-count-is-derived-from-what-it-counts` reports `a-count-is-derived-from-what-it-counts scenario passed.` The list is read by running `node -e "… require('./src/core/config.js').CONFIG_DECLARATIONS …"` — asking the module, not regexing it — and asserted to hold all six names, each of which `keel/config.yaml`'s header is then asserted to name. The derivation is proved by feeding the same rule a seventh, invented declaration the header cannot contain: it fails, the diagnostic names `invented_declaration`, and it is asserted to contain no number word. Without that step the whole scenario would be satisfied by a list that happens to agree with a header nobody compared it to.
    - M1.red: fail, for the declared reason. `a-count-is-derived-from-what-it-counts: the assertion is a literal — \`src/core/config.js\` exports no declaration list, so nothing the header is checked against comes from the code that reads it.` Carries the declared signature `the assertion is a literal`.
    - M1.green: pass. Same command after `CONFIG_DECLARATIONS` was exported and both the scenario and `delegation-resident-text` read it.
    - M2: pass. A copy of the header naming all six declarations while miscounting them in prose is accepted, so membership is the only checked property. The prose numeral stays in the header for a reader and is asserted nowhere.
    - M2.red: fail, for the declared reason, taken by restoring the property this change removes — a prose-count assertion, placed after the membership rule so it fires where M2 tests rather than where M1 does. `a-count-is-derived-from-what-it-counts: still says six declarations — a header naming all of them while miscounting them in prose was refused.` Carries the declared signature `still says six declarations`. A first attempt put the count check before membership, and its red landed on M1's assertion instead — a red for the wrong check, so the mutation was moved before the red was recorded.
    - M2.green: pass. Same command with the count assertion removed again; the miscounted header is accepted and the invented declaration is still named.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario delegation-resident-text` reports `delegation-resident-text scenario passed.` with the count literal replaced inside it by the shared rule; every `continuation`, delegation, and bootstrap clause it pins is untouched. `npm test` reports `validation --all passed: baseline plus 178 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the assertion is derived from the set and names the missing member. The derivation is proven by the one operation that can distinguish it from a coincidence — planting a member the header cannot contain — rather than by observing that the check currently passes. The absence of a count in the failure is asserted positively, by searching the diagnostic for number words, so a future author reintroducing one is caught rather than trusted not to. `delegation-resident-text` and the new scenario now share one rule, so the two cannot disagree about what the header must say, which was the shape that made the original literal expensive: the check and the document drifted apart with nothing comparing them.
      - Scope check: `git status --short` shows `src/core/config.js` and `scripts/validate_plugin.py` — two of this task's three Touch entries; `keel/config.yaml` was declared in Touch because the header had to be able to change and turned out not to need it, since the header already names all six declarations after 5.63.0. The Stop Rule held: the list is read by running the module, and no regex touches `src/core/config.js`.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the header assertion is derived from the declarations the code reads
    - E2 — the failure names the missing declaration rather than a count
    - I1
  - Read:
    - keel/CHANGELOG.md
    - openspec/specs/keel-validation-runner/spec.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-validation-runner/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted spec text. The behavior was proven red-green in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes
    - M2: `keel/CHANGELOG.md` carries an entry stating that the assertion was hand-bumped twice, what the derivation costs a future declaration, and that the prose count is deliberately no longer checked
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate a-count-is-derived-from-what-it-counts --strict` passes, and `published-specs-validate-strictly` passes
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c197ca04792bdf7db92987c2e8026431da42ef71781fbd782855c042c983a0ae
    - M1: pass. `version-alignment` passes; every marker moved 5.65.0 to 5.66.0 via `node scripts/bump_version.js minor`. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.66.0 - a count is derived from what it counts`. It states that the assertion had been hand-bumped twice and names both bumps, what the second one cost in 5.63.0 and why the `## Invalidates` entry missed it, that the check now asks the module rather than regexing it and why, and that the prose numeral is deliberately no longer asserted. It closes on what a future declaration costs: a header line and a list entry, and never again a surprise red in an unrelated scenario.
    - M3: pass. The delta is promoted into `openspec/specs/keel-validation-runner/spec.md`. `node node_modules/.bin/openspec validate a-count-is-derived-from-what-it-counts --strict` reports valid, and `published-specs-validate-strictly` reports `24 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 178 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads the markers through the scenario that checks them all. M3 asserts the promotion through both consuming tools. M2's job is that the entry records the general rule and not only this instance — the next author pinning a set as a literal is the reader this bullet is for.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, the promoted spec, and `src/core/config.js` plus `scripts/validate_plugin.py` declared complete by 1.1, plus this change's own untracked directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "the config header still says five declarations" and "the config header does not name six
  declarations" — the two count assertions inside `delegation-resident-text` in
  `scripts/validate_plugin.py`. Both are literals restating a set, and both are replaced.
  Updated by: 1.1, 2.1
- I2: "Six independent declarations live here: fast_check, …; and full_mode_paths, which names the
  paths whose change always takes the complete flow." — the header of `keel/config.yaml`. The
  enumeration stays and becomes the checked part; the numeral stays and stops being checked, which is
  a change to what the sentence is load-bearing for even though its text may not move.
  Updated by: 1.1
- I3: "an entry outside it can then be reported by name instead of being silently dropped" — the
  closed-vocabulary rationale in `src/core/config.js`. It stays true and is about `authorize:`
  entries, not about the declaration set this change exports.
  Discard reason: the wording is correct after this change.

## Expectation Coverage

- E1: The header assertion reads the declaration set from the module that defines it, not from a literal (F2, D1). Covered by: 1.1
- E2: A header missing a declaration fails naming that declaration, and no diagnostic reports a count (D2, F1). Covered by: 1.1
- E3: The prose count is deliberately unasserted, so membership is the only checked property (D3). Covered by: 1.1
- E4: The published spec and every version marker move with the behavior (I1). Covered by: 2.1
- E5: Whether a declaration read outside `src/core/config.js` would be checked (A1). Discard reason: deliberately not done rather than deferred. All six live there, a seventh elsewhere would be absent from the export and therefore unasserted in the header — which is exactly its state today rather than a regression this introduces. Guarding against it would mean the check discovering declarations by search, which is the literal problem inverted: a search that missed one would report nothing.
