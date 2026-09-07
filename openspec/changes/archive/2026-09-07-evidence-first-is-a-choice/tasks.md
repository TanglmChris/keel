# Tasks

## 1. Declared, and justified

- [x] 1.1 `verification()` stops resolving an absent strategy to `evidence-first`, and `task-start` refuses a task that declares a verification form while naming no strategy, listing the supported ones
  - Covers:
    - keel-task-capsule / Verification strategy and evidence labels are connected
    - keel-core-gates / task-start refuses an undeclared strategy and an unjustified evidence-first
    - D1
    - F1
    - F2
    - F3
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/evidence-first-is-a-choice/design.md
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-strategy-is-declared` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI against fixture repositories. A task declaring `Verify` with `M<n>` checks but no `Strategy:` line returns `fail`, and the refusal names the supported strategies; the same task declaring `Strategy: evidence-first` is not what the refusal reports, so the compiled capsule never carries a strategy the task did not name. A task declaring `Commands` in the expanded v3 form with no `Verification Strategy:` is refused the same way, because the two forms compile through one parser. A task declaring any supported strategy still passes, and an unsupported one still fails with its existing diagnostic rather than the new one.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario compact-task-authoring` passes unchanged, so the compact v4 form and its defaults are untouched apart from the strategy.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if refusing an absent strategy cannot be told apart from refusing an unsupported one, because F3 says the two are different failures and a reader who gets the wrong diagnostic looks for a typo that is not there.
    - Stop if a task that declares neither `Verify` nor `Commands` starts reporting a missing strategy, because it is already reported once as the one field it is missing and restating it is the cascade this repository has removed before.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0a986016ee2f0e86d4f099fb87655411774a8c80de20ef083b0efeb1ecf5e5a8
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-strategy-is-declared` reports `a-strategy-is-declared scenario passed.` The scenario drives the real gate against fixture repositories: a compact task declaring `Verify` with an `M<n>` check and no `Strategy:` returns `fail`, carrying the `missing-verification-strategy` code and naming the supported strategies; the same shape in the expanded v3 form, declaring `Commands` with no `Verification Strategy:`, is refused too, because both compile through one parser. Each of the five other supported strategies still passes. An unsupported strategy keeps its own `unsupported-verification-strategy` diagnostic, asserted separately so a missing strategy can never be reported as a typo. And a task declaring no verification form at all reports exactly `['missing-verification-form']` — one problem, not two.
    - M1.red: fail, for the right reason. Before `verification()` stopped supplying a default, the scenario reported `a-strategy-is-declared: a task declaring Verify with no Strategy was not refused; task-start returned 'pass'.` The red was re-taken after the assertions reached their final form — the first draft asserted on message substrings and matched the *correct* no-form message, which names the `Strategy:` field it wants written; the assertions now read diagnostic codes.
    - M1.green: pass. Same command after the `|| "evidence-first"` fallback was removed from `verification()` and `task-start` gained the `missing-verification-strategy` diagnostic: `a-strategy-is-declared scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario compact-task-authoring` reports `compact-task-authoring scenario passed.` The compact v4 form and the defaults it does inherit are unchanged; only the strategy stopped being one of them.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 157 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` Reaching that took repairing the suite's own fixtures, which is the finding below.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declared verification form without a strategy is refused, in both task forms, and that no capsule carries a strategy its task did not name. M1 proves both forms through the real CLI and asserts on diagnostic codes rather than wording, after the first draft of those assertions was shown to match a message it was not about. The two negative assertions are what make it a real check: an unsupported strategy must keep its own diagnostic, and a task with no verification form must still be reported once — the cascade this repository has removed before.
      - Scope check: `git status --short` shows exactly this task's three Touch paths plus this change's own directory. `keel guard status` reports the fingerprint unchanged from task-start; it is the same anchor recorded before this task was held, because nothing in the contract moved while it waited.
      - Findings: one, fixed in this task, and it is the measurement that matters more than the fix. **Keel's own suite carried twenty-five fixtures with no declared strategy** — `gate_task`, `task_contract_fixture`, `_goal_task_block`, and nine written inline — every one of which silently compiled to `evidence-first`. The repository that wrote the rule omitted the field twenty-five times in its own tests, which is the strongest available evidence for how invisible a default nobody is told about becomes. Each fixture now declares one; `gate_task`, `task_contract_fixture` and `_goal_task_block` declare `evidence-first`, which is what they were always getting and what they honestly are. Resolved here: M1
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `Reason:` compiles as a verification field beside `Strategy:`, and `task-start` refuses an `evidence-first` task that states no concrete reason, with no mode or tag exempting it
  - Covers:
    - keel-core-gates / task-start refuses an undeclared strategy and an unjustified evidence-first
    - D2
    - D3
    - D4
    - D5
    - F4
    - F5
    - F6
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/schemas/keel-spec-driven/templates/tasks.md
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-weakest-strategy-states-its-reason` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI against fixture repositories. An `evidence-first` task with no `Reason:` returns `fail` naming the reason as what is missing; one whose reason is an unfilled slot rather than a sentence returns `fail` the same way; one with a concrete reason passes, and the compiled capsule carries that reason inside its verification block while no `M<n>` Evidence label is created for it — asserted by reading `contract.capsule.verification` from the `--json` result and by completing the task with Evidence for its `M<n>` checks alone. A `Mode: diagnose-only` task declaring `evidence-first` with no reason is refused exactly like an `implementation` one, and a `vertical-tdd` task with no `Reason:` passes, so the requirement reaches only the strategy it is about.
    - M2: both copies of the task template — `openspec/schemas/keel-spec-driven/templates/tasks.md` and the `assets/` copy — declare a `Reason:` on their `evidence-first` example and state that the strategy must be declared, and the two files remain byte-identical.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-strategy-is-declared` passes unchanged, so task 1.1's refusal keeps its own diagnostic.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if `Reason:` cannot be kept out of the `M<n>` label mapping, because F6 shows the parser treats every non-`Strategy:` entry under `Verify` as a check and a reason that takes an Evidence label is a check the author never wrote.
    - Stop if the requirement cannot be applied to `evidence-first` alone, because D4 scopes it there and widening it to the other non-red-green strategies is a different decision than the one authorized.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:29ecb0d830071e7014a887bd2d2cda033cff0b4b3eb2a46090a49a0ab8e1d0d5
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-weakest-strategy-states-its-reason` reports `the-weakest-strategy-states-its-reason scenario passed.` Through the real gate: an `evidence-first` task with no `Reason:` returns `fail` and the refusal names the reason as what is missing; one whose reason is `TODO` and one whose reason is `<why>` are refused the same way; one stating a sentence passes, and the `--json` result's `contract.capsule.verification` carries that sentence as `reason` while its `commands` remain exactly `['M1']` — the reason is a field, not a check, so it takes no Evidence label. A `Mode: diagnose-only` task declaring `evidence-first` with no reason is refused exactly like an `implementation` one, and a `vertical-tdd` task with no reason passes.
    - M1.red: fail, for the right reason. Before `verification()` learned the field, the scenario reported `the-weakest-strategy-states-its-reason: an evidence-first task stating no reason was not refused; task-start returned 'pass'.` A `Reason:` line was itself refused at that point as `Command entry must use an M<n> label`, which is F6 — the field had to be recognized before it could be required.
    - M1.green: pass. Same command after `verification()` parsed `Reason:` beside `Strategy:`, the capsule emitted it, and `task-start` gained the `missing-evidence-first-reason` diagnostic: `the-weakest-strategy-states-its-reason scenario passed.`
    - M2: pass. Both copies of the task template now show a `Reason:` on the `evidence-first` example and state in the verification-discipline comment that Strategy is required, that nothing is supplied by default because the value an omission would select is the one with no red-green requirement, and that `evidence-first` carries a reason no mode exempts. `diff -q` reports the shipped and packaged copies byte-identical, and `tasks-template-red-green-example` gates the filled template through `task-start`, so the example cannot drift from the rule it illustrates.
    - M2.red: fail, for the right reason. Before the templates were edited, `tasks-template-red-green-example` reported `task 1.1 written from the shipped template did not pass task-start.` with `missing-evidence-first-reason` — the shipped example was a task this change refuses, and it is the example an author copies. A second red followed the first edit: the `Reason:` slot was written across two lines, and `fill_template_slots` fills a slot on one line, so the continuation was read as a command entry.
    - M2.green: pass. Same scenario after both copies gained a single-line `Reason:` slot on the `evidence-first` example, the verification-discipline comment stated that Strategy is required and unsupplied by default, and `SLOT_VOCABULARY` filled `<strategy>` with a strategy the generic task can use as written: `tasks-template-red-green-example scenario passed.`
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-strategy-is-declared` reports `a-strategy-is-declared scenario passed.` Task 1.1's refusal keeps its own `missing-verification-strategy` diagnostic; the two failures stay distinguishable.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 158 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 157 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that `evidence-first` states a concrete reason, that the reason compiles into the capsule without becoming a check, and that no mode exempts it. M1 proves all three, and the two negative halves are what make it a real check rather than a spelling test: the `diagnose-only` case is the exemption D3 refused, and the `vertical-tdd` case proves the requirement did not leak onto the other five strategies. The capsule assertion reads the compiled `verification` block rather than the task source, because the question is what the contract carries, not what the author typed.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `src/core/task-contract.js`, `scripts/validate_plugin.py`, and both template copies — plus this change's own directory. `src/core/gates.js` is declared in Touch and was not needed: the refusal belongs to the compiler, beside the strategy check it sits next to. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: two.

        First, fixed in this task. Requiring the reason broke sixty of the suite's own scenarios at once — every fixture that had been silently getting `evidence-first` now owed a sentence. That is the same measurement task 1.1 recorded, seen from the other side and larger: not only was the field omitted twenty-five times, the value it silently produced was load-bearing for a third of the suite. Each fixture now states why it has no behavior to fail first, which is true of a gate fixture and was true before anyone wrote it down. Resolved here: M4

        Second, still open, and it is about a different checker. The word `placeholder` cannot appear in a `Verify` check even as ordinary prose: this task's own M1 originally used it in a sentence describing a reason that is a slot rather than a statement, and `task-start` refused the check as unfilled. Writing this finding hit the same rule a second time, in `Evidence` — the sentence above is fenced in inline code for that reason, which is the escape the diagnostic names. That is the same false-positive family 5.42.0 fixed for the `keel --check` tasks.md rules — a word used as vocabulary read as a marker — and the lesson was applied to that checker and not to this one, which has its own `UNFILLED_TOKEN` scan. The diagnostic does name inline code as the escape, so it is recoverable; it is still a rule that refuses a sentence for containing a word about the rule. Durable owner: https://github.com/TanglmChris/keel/issues/114 — the same issue that owns the resolution-marker grammar, because both are the gate's vocabulary colliding with the prose it asks authors to write. Naming that marker in this sentence is itself the third instance: written with its colon, even inside backticks, it is read as a marker and the next word as its evidence.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the strategy is declared by the task and never supplied by the compiler
    - E2 — `evidence-first` carries a stated reason a reviewer can disagree with
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
    - openspec/specs/keel-task-capsule/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. There is no runtime behavior to fail first — the behavior this change adds was proven red-green in tasks 1.1 and 1.2, and re-proving it here would assert nothing new.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `AGENTS.md` and `assets/bootstrap/AGENTS.md` state that the strategy is declared rather than defaulted and that `evidence-first` carries a reason, and the two files stay consistent with each other
    - M3: `keel/CHANGELOG.md` carries an entry stating that the strategy was a silent default rather than a documented one, that omitting the line was how a task opted out of red-green, and the corpus proportions that show the escape hatch in use
    - M4: both spec deltas are promoted into `openspec/specs/keel-task-capsule/spec.md` and `openspec/specs/keel-core-gates/spec.md`, `node node_modules/.bin/openspec validate evidence-first-is-a-choice --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:da935535670355c8d5fc5920b5f0d849fafffa3b543b835bd56d7b461b99b8ff
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.49.0 to 5.50.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `AGENTS.md`'s verification-discipline bullet now states that nothing supplies a strategy by default and says why — the value an omission would select is the one with no red-green requirement — that a missing or unsupported strategy fails task-start, and that `evidence-first` states a `Reason:` no mode exempts. `assets/bootstrap/AGENTS.md` needed no change and is consistent by construction: it is nine lines that point at the protocol rather than restating it, which `## Invalidates` I1 now records after the first draft claimed the bullet lived in both.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.50.0 - evidence-first is a choice`. It states that omitting the line was how a task opted out of red-green and gives the two gate results that prove it, that no spec authorized the default — naming the inherited-defaults list the strategy is absent from and the scenario called *Evidence-first is explicit* — the six-repository proportions, and the fact that a task stating no reason keeps the identical capsule and fingerprint. It also records the twenty-five undeclared fixtures and the sixty scenarios the reason requirement broke, which is the measurement, not an aside.
    - M4: pass. Both deltas are promoted — `openspec/specs/keel-task-capsule/spec.md` carries the reworded requirement with its new `A strategy is never inherited` scenario, and `openspec/specs/keel-core-gates/spec.md` carries `task-start refuses an undeclared strategy and an unjustified evidence-first` with its four scenarios. `node node_modules/.bin/openspec validate evidence-first-is-a-choice --strict` reports `Change 'evidence-first-is-a-choice' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 158 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.2 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M4 asserts both promotions through the two tools that consume the published store. M2 and M3 are the prose checks. What M2 had to survive is that its first draft asserted a change to a file that did not need one — the bullet is not in the consumer bootstrap — which is recorded rather than quietly dropped, because an `## Invalidates` entry naming the wrong location is the same defect class as one naming the wrong wording. What M3 has to carry is the pair of numbers a reader cannot reconstruct: 92% in one repository against 17% in another says the strategy was being chosen by habit, and twenty-five undeclared fixtures inside Keel itself says it was often not being chosen at all.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, both promoted spec files, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/task-contract.js` and the two templates from tasks 1.1 and 1.2, already declared complete and untouched by this task, plus this change's own directory. Correcting I1's text moved no fingerprint: `keel guard status` and a re-run `task-start` both report `sha256:da93553567…`, unchanged, so an `I<n>` entry is not resolved into the capsule the way a cited `D<n>` is.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "an unsupported strategy fails task-start" — the verification discipline bullet in `AGENTS.md`.
  After this change an *absent* strategy fails too, and `evidence-first` fails without a reason, so the
  sentence names one of three refusals as if it were the only one. The consumer bootstrap asset does
  not carry this bullet; it is nine lines and points at the protocol rather than restating it.
  Updated by: 2.1
- I2: "the capsule uses `evidence-first`" — the "Evidence-first is explicit" scenario in
  `openspec/specs/keel-task-capsule/spec.md`. The capsule stops choosing the strategy at all, and the
  task declares it together with a reason.
  Updated by: 2.1
- I3: "Strategy is one of vertical-tdd," — the verification-discipline comment in both copies of
  `openspec/schemas/keel-spec-driven/templates/tasks.md`. It lists the vocabulary without saying the
  field is required or that one member of the list costs an extra line.
  Updated by: 1.2
- I4: "- Strategy: evidence-first" — the `diagnose-only` example in both copies of that same template.
  Under D3 that example becomes a task `task-start` refuses, and it is the example an author copies.
  Updated by: 1.2

## Expectation Coverage

- E1: A task that declares a verification form and no strategy is refused, in both the compact and the expanded form, and no capsule carries a strategy its task did not name. Covered by: 1.1, 2.1
- E2: An `evidence-first` task states a concrete reason, the reason compiles into the capsule without becoming a check, and no mode exempts it. Covered by: 1.2, 2.1
- E3: Every other strategy keeps its current requirements, and an unsupported strategy keeps its existing diagnostic. Covered by: 1.1, 1.2
- E4: Whether a stated reason is true. Discard reason: a gate cannot judge it, D2 records that presence and concreteness are the whole contract — the same one `Discard reason:` has — and the semantic Review together with `keel-review-checklist` is where a rote reason is called out.
