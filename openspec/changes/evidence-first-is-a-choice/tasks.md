# Tasks

## 1. Declared, and justified

- [ ] 1.1 `verification()` stops resolving an absent strategy to `evidence-first`, and `task-start` refuses a task that declares a verification form while naming no strategy, listing the supported ones
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
    - M1: not recorded. The scenario is written and passes, and its red was verified with the final assertions in place (`a-strategy-is-declared: a task declaring Verify with no Strategy was not refused; task-start returned 'pass'.` before the implementation, `a-strategy-is-declared scenario passed.` after). The result is not recorded as evidence because M3 below cannot run, and a task's checks are recorded together or not at all.
    - M2: not recorded. Same reason.
    - M3: blocked. `npm test` reports `validation --all failed for: native-goal-projection`. That failure is not this task's: it reproduces on a clean checkout of `ed1c975` with every change stashed, this change's directory moved aside, and `keel/guard.json` removed, and it reproduces with this task's `src/core/task-contract.js` reverted to main. Isolated cause: `keel ... --json` writes 11,849 bytes to a file and 8,192 through a pipe, because `bin/keel.js:2237` calls `process.exit(main())` before Node flushes an async stdout write. Filed as https://github.com/TanglmChris/keel/issues/119.
    - Review:
      - Status: blocked
      - Acceptance check: not performed. The Acceptance is proven by M1, which passes, but M3 exists to show the change breaks nothing else and it cannot answer that question while a pre-existing failure fires in the same run.
      - Scope check: `git status --short` shows this task's three Touch paths and this change's own directory. No file outside Touch was written.
      - Findings: one, still open, and it is why this task stopped. `keel`'s `--json` output is truncated at the pipe buffer, so every programmatic consumer — the plugin's `session-start.js` and `pretooluse-guard.js`, and any `keel gate ... --json | jq` in CI — silently receives a valid prefix of an incomplete document above 8KB. It surfaced here as an intermittent suite failure because parallel execution changes when the parent drains the pipe. Durable owner: https://github.com/TanglmChris/keel/issues/119
    - Blocker: the verification suite cannot answer M3 until issue #119 is fixed. This task's implementation is complete and its own scenario is green; it is held unchecked rather than recorded, because recording M3 as anything but blocked would misstate what was proven.
    - Reauthorizations: none

- [ ] 1.2 `Reason:` compiles as a verification field beside `Strategy:`, and `task-start` refuses an `evidence-first` task that states no concrete reason, with no mode or tag exempting it
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
    - M1: a new `the-weakest-strategy-states-its-reason` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI against fixture repositories. An `evidence-first` task with no `Reason:` returns `fail` naming the reason as what is missing; one whose reason is a placeholder returns `fail` the same way; one with a concrete reason passes, and the compiled capsule carries that reason inside its verification block while no `M<n>` Evidence label is created for it — asserted by reading `contract.capsule.verification` from the `--json` result and by completing the task with Evidence for its `M<n>` checks alone. A `Mode: diagnose-only` task declaring `evidence-first` with no reason is refused exactly like an `implementation` one, and a `vertical-tdd` task with no `Reason:` passes, so the requirement reaches only the strategy it is about.
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
    - Contract:
    - M1:
    - M2:
    - M3:
    - M4:

## 2. Close

- [ ] 2.1 Release
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
    - Contract:
    - M1:
    - M2:
    - M3:
    - M4:
    - M5:

## Invalidates

- I1: "an unsupported strategy fails task-start" — the verification discipline bullet in `AGENTS.md`
  and in `assets/bootstrap/AGENTS.md`. After this change an *absent* strategy fails too, and
  `evidence-first` fails without a reason, so the sentence names one of three refusals as if it were
  the only one.
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
