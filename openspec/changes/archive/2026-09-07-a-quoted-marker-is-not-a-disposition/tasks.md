# Tasks

## 1. Where a marker is written

- [x] 1.1 The `Review Findings` scan blanks inline-code spans before looking for any disposition marker, preserving offsets so every positional rule reads what it read before, and the resolution refusal names the text it took for evidence
  - Covers:
    - keel-core-gates / A quoted disposition marker is not a disposition
    - D1
    - D2
    - D3
    - D5
    - A1
    - F1
    - F2
    - F3
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-quoted-marker-is-not-a-disposition/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-quoted-marker-is-not-a-disposition` scenario in `scripts/validate_plugin.py` drives `keel gate task-complete` through the real CLI against fixture repositories whose Findings is written per case. A block naming a marker inside inline code and recording a genuine `Durable owner:` tracker reference passes, and so does the same block recording a real resolution naming a declared check — neither reports a resolution-evidence problem. A block whose only marker is quoted is refused as carrying no disposition, reporting the owner problem rather than the resolution one, so the quotation neither creates a disposition nor hides the absence of one. Each of the four markers is asserted quoted, so the treatment is not the one that fired. The forms that must keep their verdicts: an unquoted `Resolved here:` naming a declared check still passes, one naming a check the task does not declare still fails, and a `Durable owner:` naming a path that does not exist still fails by name.
    - M2: the resolution refusal names the text it read as evidence, asserted by giving a task a resolution whose evidence is an ordinary word and requiring that word to appear in the message.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario findings-resolved-here` passes unchanged, so the narrow capture D4 keeps is untouched.
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` passes unchanged, so every accepted owner form keeps its verdict.
    - M5 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if blanking shortens the scanned text, because D1 records that the existing rules read positionally and a shortened text moves what they read.
    - Stop if any text reported back to the author comes from the blanked copy, because D2 records that a diagnostic quoting it would show a sentence with holes in it.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d3c87e3d53414651200dc2d364b258422587e1db5c6580113b10994efe5daa3d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-quoted-marker-is-not-a-disposition` reports `a-quoted-marker-is-not-a-disposition scenario passed.` Through the real CLI against fixture repositories: a block naming a marker inside inline code and recording `Durable owner: https://github.com/TanglmChris/keel/issues/114` passes, and so does one recording `Resolved here: M1` beside a quoted marker. Each of the four markers is asserted quoted on its own, and a block whose only marker is quoted is refused with `finding-owner` and never `finding-resolution-evidence` — the quotation neither creates a disposition nor hides that there is none. The verdicts that must not move are asserted too: `Resolved here: M1` passes, `Resolved here: M9` fails as a check the task does not declare, and `Durable owner: docs/nowhere.md` fails by name.
    - M1.red: fail, for the right reason. Before the blanking existed, the scenario reported `a quoted marker eclipsed a genuine tracker owner; ['finding-resolution-evidence']` — the block's real disposition was a tracker owner, and the gate reported it as a resolution with unusable evidence, which is F2: the global resolution scan reaches the quoted mention first and the caller stops there.
    - M1.green: pass. Same command after `withoutQuotedMarkers()` blanked the marker vocabulary inside inline-code spans and both Findings readers took the blanked copy.
    - M2: pass. Asserted in the same scenario: a task whose Findings reads `Resolved here: thoroughly, by rewriting it.` is refused, and the message contains `thoroughly` — the word the gate read where the author believes they named a check.
    - M2.red: fail, for the right reason. Taken on its own by reverting only the message branch, leaving the blanking in place, so the red belongs to this check and not to M1's: `the refusal does not name the text it read as evidence; got 'Review Findings records a finding as resolved here, but its evidence is not usable — it names neither a check nor a path. …'` — the old message, which is exactly the sentence the author disagrees with.
    - M2.green: pass. Same command with the branch restored: `a-quoted-marker-is-not-a-disposition scenario passed.`
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario findings-resolved-here` reports `findings-resolved-here scenario passed.` The narrow capture D4 keeps is untouched.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` reports `durable-owner-vocabulary scenario passed.` Every accepted owner form keeps its verdict.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 159 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 158 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a quoted marker is not a disposition, that it does not eclipse a real one, and that a refused resolution names what it read. M1 proves the first two from both sides — a quoted marker beside a real disposition must not break it, and a quoted marker alone must not substitute for one — and asserts the distinction by problem code rather than by message text, because the defect was precisely that the wrong problem was reported. The four markers are asserted separately, so the fix is not the one that fired. M2 proves the third against the fallback branch, which is the one an author actually reaches.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, fixed in this task, and it is about how it was nearly shipped wrong. The first draft of `withoutQuotedMarkers()` blanked whole inline-code spans. That passed the new scenario, `findings-resolved-here`, `durable-owner-vocabulary`, and every other scenario in the suite — and it silently broke a supported form: a disposition whose value is wrapped in backticks, which 5.47.0 added on purpose. `Durable owner: `keel/archive/note.md`` and `Resolved here: `src/example.js`` both went from passing to failing, and nothing in 159 scenarios noticed. It was found by asking whether the blunt version could destroy a path, not by any check. The function now blanks only the marker vocabulary inside a span, and both forms are asserted in this task's own scenario so the next blunt version fails loudly. Resolved here: M1
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a quoted marker is not a disposition and does not eclipse a real one
    - E2 — a refused resolution names what it read
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The behavior this change adds was proven red-green in task 1.1, and there is nothing here that can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry stating that one quoted mention eclipsed every real disposition in the block, that the rule it applies was established in 5.42.0 and never reached this scan, and that the narrow resolution capture was deliberately left alone against the corpus measurement
    - M3: the spec delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node node_modules/.bin/openspec validate a-quoted-marker-is-not-a-disposition --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:57afa424af07f50b43a436364e35f72917c8cb472f81e1e60c12379c0f2a6a30
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.50.0 to 5.51.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.51.0 - a quoted marker is not a disposition`. It states that one quoted mention eclipsed every real disposition in the block and why — the global scan reaches it first and the caller stops there — that 5.42.0 established the rule and it had not reached this scan, and that the narrow resolution capture was deliberately kept against a 388-disposition measurement rather than widened as the report asked. It also records that the first draft of the blanking silently broke a supported form while all 158 scenarios passed.
    - M3: pass. The delta is promoted — `openspec/specs/keel-core-gates/spec.md` carries `A quoted disposition marker is not a disposition` with its four scenarios. `node node_modules/.bin/openspec validate a-quoted-marker-is-not-a-disposition --strict` reports `Change 'a-quoted-marker-is-not-a-disposition' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 159 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M3 asserts the promotion through both tools that consume the published store. M2 is the one prose check, and what it has to carry is the half of issue #114 this change *refused*: a reader who took only "the marker rule was too strict" from the entry would expect the narrow capture to have been widened, and would be surprised by the gate. The entry states the measurement that settled it and what widening would have cost.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-core-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/gates.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory. `AGENTS.md` needed no wording change: the resident protocol describes the three dispositions and never says where a marker may be written, which is the gap the promoted requirement fills.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "A path is checked for existence when it is cited" — the durable-owner vocabulary sentence in
  `src/core/gates.js`. It describes where a path is read from and says nothing about where a marker
  is read from, which is now a separate question the same field answers.
  Discard reason: the sentence stays true. It is quoted here because a reader asking what the gate
  reads out of `Findings` searches it, and after this change that answer has a second half; the
  requirement added to `openspec/specs/keel-core-gates/spec.md` is where the second half belongs, not
  in a comment about paths.
- I2: "names neither a check nor a path" — the `finding-resolution-evidence` message in
  `src/core/gates.js` and the scenarios asserting it. The message keeps that clause and gains the
  token it read, so a reader searching the old wording finds a longer sentence.
  Updated by: 1.1

## Expectation Coverage

- E1: A marker inside inline code is not read as a disposition, for every marker, and a block containing one still reports its real dispositions. Covered by: 1.1, 2.1
- E2: A refused resolution names the text it read as evidence. Covered by: 1.1, 2.1
- E3: Every form that passes today keeps passing, and every form that fails today keeps failing for the same reason. Covered by: 1.1
- E4: A resolution whose evidence does not immediately follow the marker. Discard reason: D4 records the measurement — 388 real dispositions across six repositories, and the form authors write already passes — so the narrow capture is kept, and https://github.com/TanglmChris/keel/issues/114 carries the correction to the report that claimed otherwise.
