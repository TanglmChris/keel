# Tasks

## 1. What a gate says, and when

- [x] 1.1 The declared-check set is parsed from the task's own verification form, so a reference to an `M<n>` whose declaration failed to compile is no longer reported as naming an undeclared check
  - Covers:
    - keel-core-gates / A reference is judged against what the task declares
    - D1
    - A1
    - F1
    - F2
    - F3
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-diagnostic-names-its-own-cause/design.md
  - Touch:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-reference-outlives-its-declaration` scenario in `scripts/validate_plugin.py` drives `keel gate task-complete` through the real CLI against issue #112's own minimal reproduction — a compact task whose `M2` declaration carries `<experiment_id>` and whose Findings reads `Resolved here: M2`. The unfilled-slot problems are still reported, and no problem says `M2` is a check the task does not declare. Removing the slot still passes. A reference to a check the task genuinely never declared — `Resolved here: M9` — is still refused by name, so the set narrowed to the truth rather than to everything. An expanded v3 task declaring `Commands` keeps its labels.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario findings-resolved-here` passes unchanged.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the declared set cannot be built without the compiled capsule, because F2 records that the capsule is exactly what is missing in the case that misreports.
    - Stop if a reference to a check the task never wrote stops being refused, because that trades a false positive for a false negative.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5bf0a44606070a166cbb83ad464615fc305fe5753849a0becb2bc539669e26b2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-reference-outlives-its-declaration` reports `a-reference-outlives-its-declaration scenario passed.` Against issue #112's own reproduction — a compact task whose `M2` declaration carries `<experiment_id>` and whose Findings reads `Resolved here: M2` — the unfilled-slot problems are still reported and no problem says `M2` is a check the task does not declare. The same task without the slot passes. `Resolved here: M9`, a check the task genuinely never wrote, is still refused by name, so the set narrowed to the truth and not to everything. An expanded v3 task declaring `Commands` keeps its labels.
    - M1.red: fail, for the right reason. Before `declaredCommandLabels()` existed the scenario reported `a reference to M2 was reported as undeclared because M2's own declaration failed to compile` and printed all three problems, the misleading one first — exactly the output issue #112 recorded.
    - M1.green: pass. Same command after the completion path took the task's own declarations instead of the expanded v3 field a compact task never has.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario findings-resolved-here` reports `findings-resolved-here scenario passed.`
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 161 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 160 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a reference is judged against what the task declares. M1 proves it against the reporter's own fixture, which matters because a synthesized one might not reproduce the compile failure that causes the fallback. The negative half is what makes it a real check rather than a suppression: `M9` must still be refused, or the fix would have been to stop checking. The v3 case is asserted because the field the old code read is the one v3 tasks genuinely use, and it must keep working.
      - Scope check: `git status --short` shows exactly this task's three Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, fixed in this task, and it was in the fixture rather than the product. `strategy_probe_task`'s expanded v3 form emitted `Verification Strategy` and `Reason` as entries *inside* the `Commands` list, where v3 puts them beside it. The scenario caught it on its first green run — the v3 case failed with `Command entry must use an M<n> label` — so the helper now emits task-level fields for that form. It had been wrong since the helper was written in 5.50.0 and no scenario had exercised the v3 path through it. Resolved here: M1
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `keel gate task-start` warns which checks will owe `.red` and `.green` Evidence under a red-green strategy and which are exempt, refusing nothing new
  - Covers:
    - keel-core-gates / task-start states the red-green obligation
    - D3
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-obligation-is-stated-early` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI. A `vertical-tdd` task with an untagged `M1` and a `(regression)`-tagged `M2` passes and warns, naming `M1` as owing `.red` and `.green` and `M2` as exempt. The same task under `evidence-first` passes with no such warning. The warning does not change the status: the red-green task still returns `pass`, and a task that would fail `task-start` for another reason still fails with its own problem.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario regression-check-tag` passes unchanged, so what completion requires is untouched.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if stating the obligation changes any `task-start` verdict, because D3 records it as a warning and a refusal moved forward would block a task whose author has not yet tagged a check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:af618e585b7346e9d09ea8c9fb4ce53f10c56d74f3a96d06833b3a358665c1e4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-obligation-is-stated-early` reports `the-obligation-is-stated-early scenario passed.` A `vertical-tdd` task with an untagged `M1` and a `(regression)`-tagged `M2` returns `pass` and warns: `vertical-tdd will require concrete .red and .green Evidence at completion for M1; M2 is exempt as (regression). Tag a check \`(regression)\` now if it asserts that something already green stays green, rather than discovering the obligation once the checks have been run.` The same task under `evidence-first` produces no such warning. A task with an unsupported strategy still returns `fail` carrying its own diagnostic, so the warning cannot mask a verdict.
    - M1.red: fail, for the right reason. With `redGreenObligation()` stashed out, the scenario reported `task-start did not state the red-green obligation; ''` — an empty warning list, which is the state issue #112 describes: everything needed to say it was present and nothing said it.
    - M1.green: pass. Same command with the function restored and its result joined ahead of the existing shape warnings.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario regression-check-tag` reports `regression-check-tag scenario passed.` What completion requires is untouched; only when it is first said changed.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 162 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 161 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a red-green task is told which checks owe `.red`/`.green` and which are exempt, with no verdict change. M1 asserts both halves of the naming — the owing check and the exempt one — because a warning that only said "some checks will owe evidence" would restate the rule the reporter already knew and name nothing. The two negative cases carry the verdict half: a non-red-green strategy must stay silent, and a task failing for another reason must still fail with its own problem.
      - Scope check: `git status --short` shows exactly this task's two Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, still open, and it is about this task's own `task-start` output. It warned that task 1.3 declares the same Touch set as 1.2 under a red-green strategy — the split-behavior prompt added in an earlier release. Here it is a false positive: 1.2 adds a warning and 1.3 changes a renderer, two behaviors that share two files because every gate change does. That is the third time in this repository the prompt has fired, and the second time it was wrong, which is worth recording against the day someone decides whether a shared-Touch heuristic earns its noise. It is advisory and says so in its own text, so nothing was blocked. Durable owner: https://github.com/TanglmChris/keel/issues/112
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 A gate problem may carry a shared rule explanation, printed once by the text renderer and carried by every problem in the JSON result
  - Covers:
    - keel-core-gates / A shared explanation is printed once
    - D4
    - F4
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `an-explanation-is-printed-once` scenario in `scripts/validate_plugin.py` drives `keel gate task-complete` through the real CLI against F4's fixture — a two-check `vertical-tdd` task with no red-green Evidence, which reports four problems. The rendered text contains the shared sentence exactly once, each of the four problems still names its own label and phase, and the same run with `--json` carries the explanation on every problem it belongs to. The rendered output is shorter than it was, measured against the recorded 827 characters.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` passes unchanged, so a problem carrying no explanation renders as it did.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if deduplication reaches the JSON result, because D4 records that a consumer reading problems individually would then get a payload whose content depends on position.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d504f3cd3f097d0c0d6712cf923dc2ea140e8c2ae1abfb1e74096cdda1e9332f
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-explanation-is-printed-once` reports `an-explanation-is-printed-once scenario passed.` Against issue #112's shape — a two-check `vertical-tdd` task with no red-green Evidence — the rendered text carries the shared sentence exactly once, on its own `Note:` line, while all four `Problem:` lines remain and each still names its own label and phase. The same run with `--json` carries the note on all four problems. Re-measured on the reporter's own fixture: the rendered failure went from 827 to 578 characters, a 30% reduction that matches their estimate of a third, and the saving grows with the number of checks because the repetition did.
    - M1.red: fail, for the right reason. Before `problem()` accepted a note, the scenario reported `the shared rule explanation appears 4 times in the rendered text; it belongs once per run.`
    - M1.green: pass. Same command after the red-green message was split from its rule and `renderGate` printed each distinct note once.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` reports `durable-owner-vocabulary scenario passed.` A problem carrying no note renders exactly as it did — the `note` field is emitted only when there is one, so no existing problem's shape moved.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 163 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 162 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the explanation prints once in text and is carried per problem in JSON. M1 asserts both surfaces in one run against the same fixture, which is the only way the distinction is visible — a scenario checking either alone would pass on an implementation that deduplicated everywhere or nowhere. The four `Problem:` lines are asserted to survive with their own labels, because printing the note once would be worthless if it had been achieved by collapsing the problems.
      - Scope check: `git status --short` shows exactly this task's two Touch paths plus `src/core/task-contract.js` from task 1.1, already declared complete and untouched here, plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a reference is judged against what the task declares
    - E2 — the red-green obligation is stated when the contract is accepted
    - E3 — a shared explanation is printed once
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The three behaviors were proven red-green in tasks 1.1 to 1.3, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming issue #112's three findings, the measured reproduction of each on 5.52.0, and what was deliberately not done about diagnostic ordering
    - M3: the spec delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node node_modules/.bin/openspec validate a-diagnostic-names-its-own-cause --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:90e10fc43cc8979f34fc95f33fdf675249cab789ae34e90cc9bee0baeeee7ce4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.52.0 to 5.53.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.53.0 - a diagnostic names its own cause`. It opens by saying where the three findings came from and what the reporter measured, states each defect with its reproduction — the empty declared-set and its cause, the obligation checked only at completion, the 827-character failure with four copies of one sentence — records the 827→578 re-measurement, and states what was deliberately not done about ordering and why. It also records that no verdict moved.
    - M3: pass. The delta is promoted — `openspec/specs/keel-core-gates/spec.md` carries all three requirements with their six scenarios. `node node_modules/.bin/openspec validate a-diagnostic-names-its-own-cause --strict` reports `Change 'a-diagnostic-names-its-own-cause' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 163 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.3 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M3 asserts the promotion through both tools that consume the published store. M2 is the one prose check, and what it has to carry is the provenance: these three are not defects found by reading the code, they are what one project measured over 149 invocations, and an entry that described only the fixes would lose the part that makes the next report worth filing.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-core-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files — plus `src/core/gates.js` and `src/core/task-contract.js` from tasks 1.1 to 1.3, already declared complete and untouched by this task, plus this change's own untracked directory. `AGENTS.md` needed no wording change beyond its version marker: the resident protocol states what the gates require and not what their output looks like.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "which a compact task never declares — so their absence is a fact about the fallback" — the
  comment guarding `missing-commands` in `src/core/gates.js`. After this change the fallback no longer
  returns an absence for a compact task, so the sentence describes a branch that has stopped being
  reachable that way.
  Updated by: 1.1
- I2: "M2 is not a check this task declares" — the message issue #112 reports as the misleading one.
  It stays for a reference to a check that genuinely does not exist and stops appearing for one whose
  declaration merely failed to compile.
  Updated by: 1.1

## Expectation Coverage

- E1: A reference to an `M<n>` is judged against the task's own declarations, and a reference to a check that was never written is still refused. Covered by: 1.1, 2.1
- E2: A red-green task is told at `task-start` which checks owe `.red`/`.green` and which are exempt, with no verdict change. Covered by: 1.2, 2.1
- E3: A shared rule explanation renders once in text and is carried per problem in JSON. Covered by: 1.3, 2.1
- E4: Ordering problems so a root cause precedes what it caused. Discard reason: D2 records that removing the derived report leaves nothing to order, and a gate that ranked its own diagnostics would need a causality model whose every wrong ranking would be a new instance of this defect. https://github.com/TanglmChris/keel/issues/112 owns it if derived reports are found elsewhere.
